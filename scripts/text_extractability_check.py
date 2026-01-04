import sqlite3
import fitz
from pathlib import Path


def get_db_path():
    return Path(__file__).parent.parent / "data" / "metadata" / "documents.db"


def get_pdfs_dir():
    base_dir = Path(__file__).parent.parent / "data" / "raw"
    pdfs_dir = base_dir / "pfds"
    if not pdfs_dir.exists():
        pdfs_dir = base_dir / "pdfs"
    return pdfs_dir


def log_event(conn, document_id: str, level: str, message: str):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO ingestion_logs (document_id, level, message) VALUES (?, ?, ?)",
        (document_id, level, message),
    )
    conn.commit()


def get_pending_documents(conn):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT document_id, filename, file_path FROM documents WHERE ingestion_status = 'pending'"
    )
    return cursor.fetchall()


def update_document_status(
    conn, document_id: str, status: str, rejection_reason: str = None
):
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE documents SET ingestion_status = ?, rejection_reason = ? WHERE document_id = ?",
        (status, rejection_reason, document_id),
    )
    conn.commit()


def extract_text_metrics(pdf_path: str) -> dict:
    metrics = {
        "page_count": 0,
        "total_characters": 0,
        "avg_chars_per_page": 0,
        "empty_page_ratio": 0,
        "extraction_success": False,
        "error": None,
    }

    try:
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        metrics["page_count"] = page_count

        if page_count == 0:
            doc.close()
            return metrics

        all_text = []
        empty_pages = 0

        for page in doc:
            text = page.get_text()
            all_text.append(text)
            if not text.strip():
                empty_pages += 1

        total_text = "".join(all_text)
        metrics["total_characters"] = len(total_text)
        metrics["avg_chars_per_page"] = (
            len(total_text) / page_count if page_count > 0 else 0
        )
        metrics["empty_page_ratio"] = empty_pages / page_count if page_count > 0 else 0
        metrics["extraction_success"] = True

        doc.close()

    except Exception as e:
        metrics["error"] = str(e)

    return metrics


def classify_document(metrics: dict) -> tuple[str, str]:
    page_count = metrics["page_count"]
    total_chars = metrics["total_characters"]
    avg_chars = metrics["avg_chars_per_page"]
    empty_ratio = metrics["empty_page_ratio"]
    extraction_success = metrics["extraction_success"]
    error = metrics["error"]

    if error or page_count == 0 or total_chars < 500:
        if error:
            reason = f"Extraction error: {error}"
        elif page_count == 0:
            reason = "Zero pages detected"
        else:
            reason = f"Insufficient text: {total_chars} characters (< 500)"
        return "rejected", reason

    if total_chars >= 3000 and avg_chars >= 300 and empty_ratio <= 0.2:
        return "accepted", None

    if total_chars < 1500 and page_count >= 3 and extraction_success:
        return "rejected", "needs_ocr"

    reason = f"Quality threshold failed: {total_chars} total chars, {avg_chars:.1f} avg/page, {empty_ratio:.2f} empty ratio"
    return "rejected", reason


def process_document(
    conn, document_id: str, filename: str, file_path: str, pdfs_dir: Path
) -> dict:
    full_path = (
        pdfs_dir / Path(file_path).name
        if not Path(file_path).is_absolute()
        else Path(file_path)
    )

    if not full_path.exists():
        log_event(conn, document_id, "ERROR", f"File not found: {filename}")
        update_document_status(conn, document_id, "rejected", "File not found")
        return {"status": "rejected", "error": "file_not_found"}

    metrics = extract_text_metrics(str(full_path))

    if not metrics["extraction_success"]:
        log_event(
            conn,
            document_id,
            "ERROR",
            f"Extraction failed for {filename}: {metrics['error']}",
        )
        update_document_status(
            conn, document_id, "rejected", f"Extraction error: {metrics['error']}"
        )
        return {"status": "rejected", "error": metrics["error"]}

    status, rejection_reason = classify_document(metrics)

    level = (
        "INFO"
        if status == "accepted"
        else ("WARNING" if rejection_reason == "needs_ocr" else "ERROR")
    )

    message = (
        f"File: {filename}, "
        f"Pages: {metrics['page_count']}, "
        f"Total chars: {metrics['total_characters']}, "
        f"Avg chars/page: {metrics['avg_chars_per_page']:.1f}, "
        f"Empty page ratio: {metrics['empty_page_ratio']:.2f}, "
        f"Decision: {status}"
        + (f", Reason: {rejection_reason}" if rejection_reason else "")
    )

    log_event(conn, document_id, level, message)
    update_document_status(conn, document_id, status, rejection_reason)

    return {"status": status, "metrics": metrics, "rejection_reason": rejection_reason}


def run_extractability_check():
    db_path = get_db_path()
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found at {db_path}. Run create_db.py first."
        )

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    pending_docs = get_pending_documents(conn)

    if not pending_docs:
        log_event(conn, None, "INFO", "No pending documents found")
        return {"accepted": 0, "rejected": 0, "needs_ocr": 0}

    pdfs_dir = get_pdfs_dir()

    results = {"accepted": 0, "rejected": 0, "needs_ocr": 0}

    for document_id, filename, file_path in pending_docs:
        try:
            result = process_document(conn, document_id, filename, file_path, pdfs_dir)
            status = result["status"]

            if status == "accepted":
                results["accepted"] += 1
            elif result.get("rejection_reason") == "needs_ocr":
                results["needs_ocr"] += 1
                results["rejected"] += 1
            else:
                results["rejected"] += 1

        except Exception as e:
            log_event(conn, document_id, "ERROR", f"Processing failed: {str(e)}")
            update_document_status(
                conn, document_id, "rejected", f"Processing error: {str(e)}"
            )
            results["rejected"] += 1

    summary_message = (
        f"Extractability check completed: "
        f"{results['accepted']} accepted, "
        f"{results['needs_ocr']} needs OCR, "
        f"{results['rejected'] - results['needs_ocr']} rejected"
    )
    log_event(conn, None, "INFO", summary_message)

    conn.close()

    return results


if __name__ == "__main__":
    results = run_extractability_check()
    print(f"Accepted: {results['accepted']}")
    print(f"Needs OCR: {results['needs_ocr']}")
    print(f"Rejected: {results['rejected'] - results['needs_ocr']}")
