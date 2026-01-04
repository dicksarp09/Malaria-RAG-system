from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import sys
from pathlib import Path
from typing import List
import shutil

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.models.schemas import IngestResponse

router = APIRouter(prefix="/ingest", tags=["ingestion"])

PDF_DIR = Path(__file__).parent.parent.parent / "data" / "raw" / "pfds"


@router.post("/pdfs", response_model=IngestResponse)
async def ingest_pdfs(files: List[UploadFile] = File(...)):
    """Ingest PDF files - upload and trigger ingestion pipeline."""

    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    if not PDF_DIR.exists():
        PDF_DIR.mkdir(parents=True, exist_ok=True)

    saved_files = []

    for file in files:
        file_path = PDF_DIR / file.filename

        if file_path.exists():
            continue

        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(file.filename)
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Error saving {file.filename}: {str(e)}",
                    "documents_processed": 0,
                    "duplicates_skipped": 0,
                    "errors": 1,
                },
            )

    if not saved_files:
        return IngestResponse(
            success=True,
            message="All files were duplicates and were skipped",
            documents_processed=0,
            duplicates_skipped=len(files),
            errors=0,
        )

    return IngestResponse(
        success=True,
        message=f"Successfully uploaded {len(saved_files)} files. Run ingestion pipeline to process.",
        documents_processed=len(saved_files),
        duplicates_skipped=len(files) - len(saved_files),
        errors=0,
    )
