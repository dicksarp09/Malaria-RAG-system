import sqlite3
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from prometheus_client import Counter, Gauge, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel

load_dotenv()

# Initialize LangSmith if available
LANGSMITH_ENABLED = False
try:
    sys.path.append(str(Path(__file__).parent.parent / "scripts"))
    from simple_langsmith_v3 import LANGSMITH_ENABLED as langsmith_ok
    from simple_langsmith_v3 import log_query

    LANGSMITH_ENABLED = langsmith_ok
except Exception as e:
    LANGSMITH_ENABLED = False
    print(f"[LangSmith] Not available: {e}")

app = FastAPI(
    title="Malaria RAG API",
    description="Backend API for Malaria Research RAG System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

DB_PATH = Path(__file__).parent.parent / "data" / "metadata" / "documents.db"

query_counter = Counter("rag_queries_total", "Total number of RAG queries", ["country", "status"])

query_duration = Histogram(
    "rag_query_duration_seconds", "RAG query duration in seconds", ["country"]
)

retrieved_chunks_gauge = Gauge("rag_retrieved_chunks", "Number of chunks retrieved in last query")

llm_latency_histogram = Histogram("rag_llm_latency_seconds", "LLM response latency in seconds")


class QueryRequest(BaseModel):
    user_query: str
    country: str | None = None
    top_k: int = 10


class ChunkMetadata(BaseModel):
    chunk_id: str
    document_id: str
    section: str
    text: str
    char_count: int
    final_score: float
    semantic_score: float
    bm25_score: float
    country: str | None = None


class QueryResponse(BaseModel):
    query: str
    answer: str
    retrieved_chunks: list[ChunkMetadata]
    top_chunk_ids: list[str]
    chunks_retrieved: int
    is_insufficient_evidence: bool


@app.get("/")
async def root():
    return {
        "message": "Malaria RAG API",
        "version": "1.0.0",
        "langsmith_tracing": LANGSMITH_ENABLED,
        "endpoints": {"query": "/query", "health": "/health"},
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "langsmith_tracing": LANGSMITH_ENABLED}


@app.post("/query")
async def query_rag(request: QueryRequest):
    """Execute RAG query with filters."""

    if not request.user_query or len(request.user_query.strip()) < 3:
        raise HTTPException(status_code=400, detail="Query must be at least 3 characters")

    query_start = time.time()
    country = request.country or "unknown"

    try:
        sys.path.append(str(Path(__file__).parent))

        from hybrid_retrieval import HybridRetriever

        retriever = HybridRetriever()
        chunks = retriever.retrieve(
            query=request.user_query, country=request.country, K=request.top_k
        )

        retrieved_chunks_gauge.set(len(chunks))

        context_parts = []
        chunk_texts = {}

        for chunk in chunks:
            chunk_id = chunk.get("chunk_id", "")
            payload = chunk.get("payload", {})

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT text FROM chunks WHERE chunk_id = ?", (chunk_id,))
            result = cursor.fetchone()
            conn.close()

            section = payload.get("section", "")
            country = payload.get("country", "")
            doc_id = payload.get("document_id", "")

            if result:
                chunk_text = result[0]
                chunk_texts[chunk_id] = chunk_text
                context_parts.append(
                    f"[Section: {section}] [Country: {country}] [Document ID: {doc_id}]\n{chunk_text}"
                )

        context = "\n\n".join(context_parts)

        client = Groq()
        llm_start = time.time()
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a research assistant. Answer query strictly based on provided evidence from malaria research papers. Use citations for every statement [Document ID: id] [Section: section]. Do not invent information. If evidence is missing or ambiguous, respond with: INSUFFICIENT EVIDENCE.",
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {request.user_query}\n\nAnswer:",
                },
            ],
            max_tokens=1024,
            temperature=0.1,
        )
        answer = completion.choices[0].message.content
        llm_latency_ms = (time.time() - llm_start) * 1000
        llm_latency_seconds = llm_latency_ms / 1000
        llm_latency_histogram.observe(llm_latency_seconds)

        is_insufficient = answer and "INSUFFICIENT EVIDENCE" in answer.upper()

        chunks_metadata = []
        for chunk in chunks:
            chunk_id = chunk.get("chunk_id", "")
            payload = chunk.get("payload", {})
            chunks_metadata.append(
                {
                    "chunk_id": chunk_id,
                    "document_id": payload.get("document_id", ""),
                    "section": payload.get("section", ""),
                    "text": chunk_texts.get(chunk_id, ""),
                    "char_count": payload.get("char_count", 0),
                    "final_score": chunk.get("final_score", 0.0),
                    "semantic_score": chunk.get("semantic_score", 0.0),
                    "bm25_score": chunk.get("bm25_score", 0.0),
                    "country": payload.get("country"),
                }
            )

        if LANGSMITH_ENABLED:
            total_latency = (time.time() - llm_start) * 1000
            log_query(
                query=request.user_query,
                country=request.country,
                top_k=request.top_k,
                chunks_retrieved=len(chunks),
                is_insufficient=is_insufficient,
                latency_ms=total_latency,
                answer=answer or "",
            )

        query_duration.observe(time.time() - query_start, labels={"country": country})
        query_counter.labels(country=country, status="success").inc()

        return QueryResponse(
            query=request.user_query,
            answer=answer or "",
            retrieved_chunks=chunks_metadata,
            top_chunk_ids=[c["chunk_id"] for c in chunks[: request.top_k]],
            chunks_retrieved=len(chunks),
            is_insufficient_evidence=bool(is_insufficient),
        )

    except Exception as e:
        query_counter.labels(country=country, status="error").inc()
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}") from None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
