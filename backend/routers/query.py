from fastapi import APIRouter, HTTPException
from typing import List, Optional
import sys
import sqlite3
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.models.schemas import QueryRequest, QueryResponse
from scripts.llm_rag_query import rag_query

router = APIRouter(prefix="/query", tags=["query"])


def get_db_path():
    return Path(__file__).parent.parent.parent / "data" / "metadata" / "documents.db"


@router.post("", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Execute RAG query with filters."""

    if not request.user_query or len(request.user_query.strip()) < 3:
        raise HTTPException(
            status_code=400, detail="Query must be at least 3 characters"
        )

    try:
        response = rag_query(
            user_query=request.user_query, country=request.country, top_k=request.top_k
        )

        conn = sqlite3.connect(get_db_path())

        chunks_metadata = []
        for chunk in response.get("retrieved_chunks", []):
            chunk_id = chunk.get("chunk_id")

            cursor = conn.cursor()
            cursor.execute("SELECT text FROM chunks WHERE chunk_id = ?", (chunk_id,))
            result = cursor.fetchone()
            chunk_text = result[0] if result else ""

            chunks_metadata.append(
                {
                    "chunk_id": chunk_id,
                    "document_id": chunk.get("payload", {}).get("document_id"),
                    "section": chunk.get("payload", {}).get("section"),
                    "text": chunk_text,
                    "char_count": chunk.get("payload", {}).get("char_count"),
                    "final_score": chunk.get("final_score", 0.0),
                    "semantic_score": chunk.get("semantic_score", 0.0),
                    "bm25_score": chunk.get("bm25_score", 0.0),
                    "country": chunk.get("payload", {}).get("country"),
                    "section_boost": chunk.get("section_boost", 0.0),
                }
            )

        conn.close()

        return QueryResponse(
            query=response["query"],
            answer=response["answer"],
            retrieved_chunks=chunks_metadata,
            top_chunk_ids=response["top_chunk_ids"],
            chunks_retrieved=response["chunks_retrieved"],
            is_insufficient_evidence=response["is_insufficient_evidence"],
            filters_applied=response["filters_applied"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
