from fastapi import APIRouter
import sys
from pathlib import Path
from typing import Optional, List

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.models.schemas import LogsResponse, LogEntry

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("", response_model=LogsResponse)
async def get_logs(level: Optional[str] = None, limit: int = 100, offset: int = 0):
    """Get ingestion and retrieval logs."""

    import sqlite3

    db_path = Path(__file__).parent.parent.parent / "data" / "metadata" / "documents.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        query = (
            "SELECT log_id, document_id, level, message, created_at FROM ingestion_logs"
        )
        params = []

        if level:
            query += " WHERE level = ?"
            params.append(level.upper())

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        logs = []
        for row in rows:
            logs.append(
                LogEntry(
                    log_id=row[0],
                    document_id=row[1],
                    level=row[2],
                    message=row[3],
                    created_at=row[4],
                )
            )

        cursor.execute("SELECT COUNT(*) FROM ingestion_logs")
        total_logs = cursor.fetchone()[0]

        conn.close()

        return LogsResponse(total_logs=total_logs, logs=logs)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch logs: {str(e)}")
