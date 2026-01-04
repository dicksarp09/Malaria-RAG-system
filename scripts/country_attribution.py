import sqlite3
import fitz
from pathlib import Path
from typing import Dict, List, Tuple, Optional


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


def get_accepted_documents(conn):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT document_id, filename, file_path FROM documents WHERE ingestion_status = 'accepted' AND country IS NULL"
    )
    return cursor.fetchall()


def update_document_country(
    conn,
    document_id: str,
    country: str,
    confidence: float,
    status: str,
    rejection_reason: str = None,
):
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE documents SET country = ?, country_confidence = ?, ingestion_status = ?, rejection_reason = ? WHERE document_id = ?",
        (country, confidence, status, rejection_reason, document_id),
    )
    conn.commit()


def extract_document_text(pdf_path: str) -> Dict[str, str]:
    sections = {"full_text": "", "title": "", "abstract": "", "affiliations": ""}

    try:
        doc = fitz.open(pdf_path)
        all_text = []

        for page in doc:
            text = page.get_text()
            all_text.append(text)

        sections["full_text"] = " ".join(all_text)

        full_text_lower = sections["full_text"].lower()

        title_keywords = ["title", "title:", "title -", "title:"]
        for keyword in title_keywords:
            idx = full_text_lower.find(keyword)
            if idx != -1:
                title_start = idx + len(keyword)
                title_end = full_text_lower.find("\n", title_start)
                if title_end != -1:
                    sections["title"] = sections["full_text"][
                        title_start:title_end
                    ].strip()
                    break

        abstract_keywords = [
            "abstract",
            "abstract:",
            "abstract -",
            "summary",
            "summary:",
        ]
        for keyword in abstract_keywords:
            idx = full_text_lower.find(keyword)
            if idx != -1:
                abstract_start = idx + len(keyword)
                abstract_end = full_text_lower.find("\n\n", abstract_start)
                if abstract_end != -1:
                    sections["abstract"] = sections["full_text"][
                        abstract_start:abstract_end
                    ].strip()
                    break

        affiliation_keywords = [
            "affiliation",
            "affiliations",
            "institution",
            "institutions",
            "address",
            "corresponding author",
        ]
        for keyword in affiliation_keywords:
            idx = full_text_lower.find(keyword)
            if idx != -1:
                aff_start = idx
                aff_end = full_text_lower.find("\n\n", aff_start)
                if aff_end != -1:
                    sections["affiliations"] = sections["full_text"][
                        aff_start:aff_end
                    ].strip()
                    break

        doc.close()

    except Exception as e:
        sections["full_text"] = ""

    return sections


def detect_country(text: str) -> Dict[str, any]:
    ghana_indicators = [
        "ghana",
        "accra",
        "kumasi",
        "tamale",
        "takoradi",
        "university of ghana",
        "kwame nkrumah university",
        "ghana health service",
        "korle bu",
        "legon",
        "ashanti",
        "greater accra",
    ]

    nigeria_indicators = [
        "nigeria",
        "abuja",
        "lagos",
        "kano",
        "ibadan",
        "port harcourt",
        "kaduna",
        "benin city",
        "university of ibadan",
        "university of lagos",
        "ahmadu bello university",
        "nigeria centre",
        "federal ministry",
        "nigeria medical",
        "nig",
    ]

    text_lower = text.lower()

    ghana_matches = []
    nigeria_matches = []

    for indicator in ghana_indicators:
        if indicator in text_lower:
            count = text_lower.count(indicator)
            ghana_matches.append((indicator, count))

    for indicator in nigeria_indicators:
        if indicator in text_lower:
            count = text_lower.count(indicator)
            nigeria_matches.append((indicator, count))

    return {
        "ghana_detected": len(ghana_matches) > 0,
        "nigeria_detected": len(nigeria_matches) > 0,
        "ghana_matches": ghana_matches,
        "nigeria_matches": nigeria_matches,
        "ghana_count": sum(m[1] for m in ghana_matches),
        "nigeria_count": sum(m[1] for m in nigeria_matches),
    }


def calculate_confidence(
    sections: Dict[str, str], detection: Dict[str, any]
) -> Tuple[float, str]:
    high_confidence_sections = ["title", "affiliations"]
    medium_confidence_sections = ["abstract"]

    ghana_in_high = any(
        detection["ghana_detected"]
        and any(m[0] in sections[section].lower() for m in detection["ghana_matches"])
        for section in high_confidence_sections
        if sections[section]
    )

    nigeria_in_high = any(
        detection["nigeria_detected"]
        and any(m[0] in sections[section].lower() for m in detection["nigeria_matches"])
        for section in high_confidence_sections
        if sections[section]
    )

    if ghana_in_high or nigeria_in_high:
        return 1.0, "title/affiliations"

    ghana_in_medium = any(
        detection["ghana_detected"]
        and any(m[0] in sections[section].lower() for m in detection["ghana_matches"])
        for section in medium_confidence_sections
        if sections[section]
    )

    nigeria_in_medium = any(
        detection["nigeria_detected"]
        and any(m[0] in sections[section].lower() for m in detection["nigeria_matches"])
        for section in medium_confidence_sections
        if sections[section]
    )

    if ghana_in_medium or nigeria_in_medium:
        return 0.5, "abstract/methods"

    if detection["ghana_detected"] or detection["nigeria_detected"]:
        return 0.5, "full text"

    return 0.0, "none"


def classify_country(sections: Dict[str, str]) -> Dict[str, any]:
    detection = detect_country(sections["full_text"])

    confidence, source = calculate_confidence(sections, detection)

    if confidence == 0.0:
        return {
            "country": None,
            "confidence": 0.0,
            "status": "rejected",
            "rejection_reason": "country_not_detected",
            "source": "none",
            "detection": detection,
        }

    if detection["ghana_detected"] and detection["nigeria_detected"]:
        country = "Ghana|Nigeria"
    elif detection["ghana_detected"]:
        country = "Ghana"
    elif detection["nigeria_detected"]:
        country = "Nigeria"
    else:
        country = None
        confidence = 0.0

    status = "rejected" if confidence == 0.0 else "accepted"
    rejection_reason = "country_not_detected" if confidence == 0.0 else None

    return {
        "country": country,
        "confidence": confidence,
        "status": status,
        "rejection_reason": rejection_reason,
        "source": source,
        "detection": detection,
    }


def process_document(
    conn, document_id: str, filename: str, file_path: str, pdfs_dir: Path
) -> Dict[str, any]:
    full_path = (
        pdfs_dir / Path(file_path).name
        if not Path(file_path).is_absolute()
        else Path(file_path)
    )

    if not full_path.exists():
        log_event(conn, document_id, "ERROR", f"File not found: {filename}")
        update_document_country(
            conn, document_id, None, 0.0, "rejected", "File not found"
        )
        return {"status": "rejected", "country": None, "confidence": 0.0}

    sections = extract_document_text(str(full_path))

    if not sections["full_text"]:
        log_event(
            conn, document_id, "ERROR", f"Failed to extract text from: {filename}"
        )
        update_document_country(
            conn, document_id, None, 0.0, "rejected", "Text extraction failed"
        )
        return {"status": "rejected", "country": None, "confidence": 0.0}

    result = classify_country(sections)

    level = (
        "INFO"
        if result["confidence"] == 1.0
        else ("WARNING" if result["confidence"] > 0 else "ERROR")
    )

    message = (
        f"File: {filename}, "
        f"Country: {result['country'] if result['country'] else 'None'}, "
        f"Confidence: {result['confidence']:.1f}, "
        f"Source: {result['source']}, "
        f"Decision: {result['status']}"
    )

    log_event(conn, document_id, level, message)
    update_document_country(
        conn,
        document_id,
        result["country"],
        result["confidence"],
        result["status"],
        result["rejection_reason"],
    )

    return {
        "status": result["status"],
        "country": result["country"],
        "confidence": result["confidence"],
    }


def run_country_attribution():
    db_path = get_db_path()
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found at {db_path}. Run create_db.py first."
        )

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    accepted_docs = get_accepted_documents(conn)

    if not accepted_docs:
        log_event(conn, None, "INFO", "No accepted documents found")
        return {"accepted": 0, "rejected": 0, "partial": 0}

    pdfs_dir = get_pdfs_dir()

    results = {"accepted": 0, "rejected": 0, "partial": 0}

    for document_id, filename, file_path in accepted_docs:
        try:
            result = process_document(conn, document_id, filename, file_path, pdfs_dir)

            if result["status"] == "accepted":
                if result["confidence"] == 1.0:
                    results["accepted"] += 1
                else:
                    results["partial"] += 1
            else:
                results["rejected"] += 1

        except Exception as e:
            log_event(conn, document_id, "ERROR", f"Processing failed: {str(e)}")
            update_document_country(
                conn, document_id, None, 0.0, "rejected", f"Processing error: {str(e)}"
            )
            results["rejected"] += 1

    summary_message = (
        f"Country attribution completed: "
        f"{results['accepted']} high confidence, "
        f"{results['partial']} partial confidence, "
        f"{results['rejected']} rejected"
    )
    log_event(conn, None, "INFO", summary_message)

    conn.close()

    return results


if __name__ == "__main__":
    results = run_country_attribution()
    print(f"High confidence: {results['accepted']}")
    print(f"Partial confidence: {results['partial']}")
    print(f"Rejected: {results['rejected']}")
