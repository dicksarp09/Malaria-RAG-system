from fastapi import APIRouter, HTTPException
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.models.schemas import RebuildRequest, RebuildResponse

router = APIRouter(prefix="/chunks", tags=["chunks"])


@router.post("/rebuild", response_model=RebuildResponse)
async def rebuild_chunks(request: RebuildRequest):
    """Rebuild chunks and embeddings from documents."""

    if not request.confirm:
        raise HTTPException(
            status_code=400, detail="Set confirm=True to rebuild chunks"
        )

    try:
        import subprocess

        result = subprocess.run(
            ["python", "scripts/chunk_documents.py"],
            cwd=str(Path(__file__).parent.parent.parent),
            capture_output=True,
            text=True,
            timeout=600,
        )

        if result.returncode != 0:
            return RebuildResponse(
                success=False,
                message=f"Chunking failed: {result.stderr}",
                chunks_rebuilt=0,
                embeddings_recreated=0,
            )

        embed_result = subprocess.run(
            ["python", "scripts/embed_chunks.py"],
            cwd=str(Path(__file__).parent.parent.parent),
            capture_output=True,
            text=True,
            timeout=600,
        )

        chunks_count = result.stdout.count("Processed:") if result.stdout else 0
        embed_count = (
            embed_result.stdout.count("Processed:") if embed_result.stdout else 0
        )

        return RebuildResponse(
            success=True,
            message=f"Successfully rebuilt chunks and embeddings",
            chunks_rebuilt=chunks_count,
            embeddings_recreated=embed_count,
        )

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Rebuild timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rebuild failed: {str(e)}")
