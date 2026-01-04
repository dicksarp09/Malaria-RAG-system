from fastapi import APIRouter, HTTPException
from typing import List
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.models.schemas import EvaluationMetrics

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.get("/metrics", response_model=EvaluationMetrics)
async def get_evaluation_metrics():
    """Get evaluation metrics from logs."""

    import sqlite3

    db_path = Path(__file__).parent.parent.parent / "data" / "metadata" / "documents.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM ingestion_logs WHERE message LIKE 'LLM Query:%'"
        )
        total_queries = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM ingestion_logs WHERE message LIKE '%Refusal: False%'"
        )
        sufficient_queries = cursor.fetchone()[0]

        insufficient_queries = total_queries - sufficient_queries

        refusal_rate = (
            (insufficient_queries / total_queries) if total_queries > 0 else 0
        )

        cursor.execute(
            "SELECT AVG(CAST(SUBSTR(message, INSTR(message, 'Chunks retrieved:') + 16, INSTR(SUBSTR(message, INSTR(message, 'Chunks retrieved:') + 16), ',') - 1) AS REAL)) FROM ingestion_logs WHERE message LIKE 'LLM Query:%'"
        )
        avg_chunks = cursor.fetchone()[0] or 0

        cursor.execute(
            "SELECT SUBSTR(SUBSTR(message, INSTR(message, 'Section:') + 9), INSTR(SUBSTR(message, INSTR(message, 'Section:') + 9), '-') - 1) as section, COUNT(*) as count FROM ingestion_logs WHERE message LIKE '%Section: %' GROUP BY section ORDER BY count DESC LIMIT 5"
        )
        top_sections = []
        for row in cursor.fetchall():
            top_sections.append({"section": row[0], "count": row[1]})

        conn.close()

        return EvaluationMetrics(
            total_queries=total_queries,
            sufficient_evidence_queries=sufficient_queries,
            insufficient_evidence_queries=insufficient_queries,
            refusal_rate=round(refusal_rate, 2),
            avg_chunks_per_query=round(avg_chunks, 2) if avg_chunks else 0,
            top_sections=top_sections,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch metrics: {str(e)}"
        )
