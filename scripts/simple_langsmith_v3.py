"""
Simple LangSmith tracer using @traceable decorator
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from langsmith import traceable

# Load .env from backend directory
env_path = Path(__file__).parent.parent / "backend" / ".env"
load_dotenv(env_path)

# Track latencies for percentile calculations
latency_history = []


def calculate_percentiles(latencies):
    """Calculate p50, p90, p95, p99 percentiles"""
    if not latencies:
        return {"p50_ms": 0, "p90_ms": 0, "p95_ms": 0, "p99_ms": 0}

    sorted_latencies = sorted(latencies)
    n = len(sorted_latencies)

    def get_percentile(p):
        idx = int(n * p / 100)
        return sorted_latencies[min(idx, n - 1)]

    return {
        "p50_ms": round(get_percentile(50), 2),
        "p90_ms": round(get_percentile(90), 2),
        "p95_ms": round(get_percentile(95), 2),
        "p99_ms": round(get_percentile(99), 2),
        "sample_count": len(latencies),
    }


# Check if LangSmith is enabled
LANGSMITH_ENABLED = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"

if LANGSMITH_ENABLED:
    api_key = os.getenv("LANGCHAIN_API_KEY")
    project = os.getenv("LANGCHAIN_PROJECT", "malaria-rag-system")

    if not api_key:
        print("[LangSmith] ERROR: LANGCHAIN_API_KEY not set")
        LANGSMITH_ENABLED = False
    else:
        print(f"[LangSmith] Connected to project: {project}")
else:
    print("[LangSmith] Disabled (set LANGCHAIN_TRACING_V2=true)")


@traceable(name="rag_query", run_type="chain")
def trace_rag_query(
    query: str,
    country: str,
    top_k: int,
    chunks_retrieved: int,
    is_insufficient: bool,
    latency_ms: float,
    answer: str,
    percentiles: dict,
) -> dict:
    """Trace a RAG query operation with clean formatting"""
    answer_preview = answer[:300] + "..." if len(answer) > 300 else answer

    result = {
        "result": {
            "answer": answer_preview,
            "status": "INSUFFICIENT_EVIDENCE" if is_insufficient else "SUCCESS",
        },
        "metrics": {
            "latency_seconds": round(latency_ms / 1000, 2),
            "chunks_retrieved": chunks_retrieved,
        },
        "query_info": {
            "original_query": query,
            "country_filter": country or "All",
            "top_k": top_k,
        },
    }

    # Add percentiles if available
    if percentiles and percentiles.get("p50_ms", 0) > 0:
        result["percentiles"] = percentiles

    return result


def log_query(
    query: str,
    country: str,
    top_k: int,
    chunks_retrieved: int,
    is_insufficient: bool,
    latency_ms: float,
    answer: str,
):
    """Log a RAG query to LangSmith with percentiles"""
    if not LANGSMITH_ENABLED:
        return None

    try:
        # Track latency
        latency_history.append(latency_ms)

        # Calculate percentiles
        percentiles = calculate_percentiles(latency_history)

        result = trace_rag_query(
            query=query,
            country=country,
            top_k=top_k,
            chunks_retrieved=chunks_retrieved,
            is_insufficient=is_insufficient,
            latency_ms=latency_ms,
            answer=answer,
            percentiles=percentiles,
        )

        print(f"[LangSmith] Query traced: {query[:50]}...")
        if percentiles["p50_ms"] > 0:
            print(
                f"[LangSmith] Percentiles (ms) - P50: {percentiles['p50_ms']}, P90: {percentiles['p90_ms']}, P95: {percentiles['p95_ms']}, P99: {percentiles['p99_ms']}"
            )

        return result
    except Exception as e:
        print(f"[LangSmith] Failed to trace query: {e}")
        return None
