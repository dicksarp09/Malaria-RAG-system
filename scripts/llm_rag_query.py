import os
from groq import Groq
from pathlib import Path
import sys
import sqlite3
import json
from typing import List, Dict, Optional
from datetime import datetime
import time

# Import hybrid_retrieval - use absolute import when running as package
try:
    from hybrid_retrieval import HybridRetriever
except ImportError:
    from scripts.hybrid_retrieval import HybridRetriever

# Import LangSmith tracing
try:
    from langsmith_tracing import RAGTracer

    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    print(
        "[LangSmith] Not available - install with: pip install langsmith langchain langchain-community"
    )


def get_db_path():
    return Path(__file__).parent.parent / "data" / "metadata" / "documents.db"


def log_event(conn, document_id: str, level: str, message: str):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO ingestion_logs (document_id, level, message) VALUES (?, ?, ?)",
        (document_id, level, message),
    )
    conn.commit()


def assemble_context(chunks: List[Dict]) -> str:
    context_parts = []

    for chunk in chunks:
        chunk_id = chunk.get("chunk_id", "")
        payload = chunk.get("payload", {})

        section = payload.get("section", "unknown")
        country = payload.get("country", "unknown")
        document_id = payload.get("document_id", "")

        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT text FROM chunks WHERE chunk_id = ?", (chunk_id,))
        result = cursor.fetchone()
        conn.close()

        chunk_text = result[0] if result else ""

        formatted_chunk = (
            f"[Section: {section}] "
            f"[Country: {country}] "
            f"[Document ID: {document_id}]\n"
            f"{chunk_text}"
        )

        context_parts.append(formatted_chunk)

    return "\n\n".join(context_parts)


def generate_system_prompt() -> str:
    return """You are a research assistant specializing in malaria research papers from Ghana and Nigeria.

IMPORTANT INSTRUCTIONS:
1. Answer the query STRICTLY based on the provided evidence from research papers.
2. Use citations for EVERY statement: [Document ID: <id>] [Section: <section>]
3. NEVER make clinical diagnoses or prescribe treatments.
4. If the evidence is insufficient, missing, or ambiguous, respond with: "INSUFFICIENT EVIDENCE"
5. Do not invent information or use outside knowledge.
6. Synthesize information from multiple chunks when appropriate.
7. Prioritize Results and Methods sections over other sections for evidence.
8. Be concise and focus on directly answering the question.

Your role is to retrieve and synthesize information from the provided research context, not to provide medical advice."""


def query_llm(client: Groq, user_query: str, context: str) -> str:
    system_prompt = generate_system_prompt()

    user_prompt = f"""Context:
{context}

Question: {user_query}

Answer:"""

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1024,
        temperature=0.1,
    )

    return completion.choices[0].message.content


def rag_query(
    user_query: str,
    country: Optional[str] = None,
    top_k: int = 10,
    log_to_db: bool = True,
) -> Dict:
    import time

    from langsmith_tracing import RAGTracer

    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA foreign_keys = ON")

    tracer = None
    if LANGSMITH_AVAILABLE:
        try:
            tracer = RAGTracer()
        except:
            pass

    start_time = time.time()

    retriever = HybridRetriever()
    chunks = retriever.retrieve(
        query=user_query, country=country, K=top_k, log_retrieval=log_to_db
    )

    retrieval_time_ms = (time.time() - start_time) * 1000

    if tracer:
        try:
            tracer.log_retrieval(user_query, chunks, retrieval_time_ms)
        except:
            pass

    context = assemble_context(chunks)

    api_key = os.environ.get(
        "GROQ_API_KEY", "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"
    )
    client = Groq(api_key=api_key)

    llm_start = time.time()
    answer = query_llm(client, user_query, context)
    llm_latency_ms = (time.time() - llm_start) * 1000

    is_insufficient = "INSUFFICIENT EVIDENCE" in answer.upper()

    total_latency_ms = (time.time() - start_time) * 1000

    if tracer:
        try:
            tracer.log_query(
                query=user_query,
                country=country,
                top_k=top_k,
                chunks_retrieved=len(chunks),
                is_insufficient=is_insufficient,
                latency_ms=total_latency_ms,
                answer=answer
            )
            tracer.log_llm_call(user_query, context, answer, llm_latency_ms)
        except:
            pass

    if log_to_db:
        filter_info = f"country={country}" if country else "none"
        refusal_info = " - INSUFFICIENT EVIDENCE" if is_insufficient else ""

        message = (
            f'LLM Query: "{user_query[:100]}...", '
            f"Chunks retrieved: {len(chunks)}, '
            f"Filters: {filter_info}, "
            f"Refusal: {is_insufficient}"
        )

        log_event(
            conn,
            chunks[0]["payload"]["document_id"] if chunks else "",
            "INFO",
            message,
        )

    conn.close()

    response = {
        "query": user_query,
        "answer": answer,
        "retrieved_chunks": chunks,
        "top_chunk_ids": [c["chunk_id"] for c in chunks[:top_k]],
        "chunks_retrieved": len(chunks),
        "is_insufficient_evidence": is_insufficient,
        "filters_applied": {"country": country, "top_k": top_k},
    }

    return response


def main():
    print("=" * 80)
    print("Medical RAG System - Malaria Research Query")
    print("=" * 80)

    queries = [
        {
            "query": "What are the most effective malaria treatment strategies in Ghana?",
            "country": "Ghana",
            "top_k": 5,
        },
        {
            "query": "How does drug resistance affect malaria treatment outcomes in Nigeria?",
            "country": "Nigeria",
            "top_k": 5,
        },
        {
            "query": "What are the prevention strategies for childhood malaria?",
            "country": None,
            "top_k": 5,
        },
        {
            "query": "What is the efficacy of artemisinin-based combination therapies?",
            "country": None,
            "top_k": 5,
        },
    ]

    for i, query_info in enumerate(queries, 1):
        print(f"\n{'=' * 80}")
        print(f"Query {i}: {query_info['query']}")
        print(f"{'=' * 80}")

        if query_info["country"]:
            print(f"Country Filter: {query_info['country']}")

        print(f"\nRetrieving chunks...")

        response = rag_query(
            user_query=query_info["query"],
            country=query_info["country"],
            top_k=query_info["top_k"],
        )

        print(f"\nChunks Retrieved: {response['chunks_retrieved']}")

        if response["is_insufficient_evidence"]:
            print(f"\nWARNING: {response['answer']}")
        else:
            print(f"\nAnswer:\n")
            print(response["answer"])

        print(f"\nTop Sources:")
        for j, chunk_id in enumerate(response["top_chunk_ids"][:3], 1):
            chunk = next(
                (c for c in response["retrieved_chunks"] if c["chunk_id"] == chunk_id),
                None,
            )
            if chunk:
                payload = chunk.get("payload", {})
                print(
                    f"  {j}. [{payload.get('section', 'N/A')}] {payload.get('country', 'N/A')} - Score: {chunk['final_score']:.4f}"
                )

    print("\n" + "=" * 80)
    print("Query session completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
