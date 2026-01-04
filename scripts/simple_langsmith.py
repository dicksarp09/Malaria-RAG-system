"""
Simple LangSmith Tracer for Malaria RAG System
Minimal dependencies approach for easy integration
"""

import os
from typing import Optional
from datetime import datetime
from pathlib import Path


# Load .env file manually
def load_env_file():
    env_path = Path(__file__).parent.parent / "backend" / ".env"
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
        print(f"Loaded .env from: {env_path}")
        return True
    else:
        print(f"ERROR: .env not found at: {env_path}")
        return False


# Load environment on import
load_env_file()


def init_langsmith():
    """Initialize LangSmith tracing"""
    try:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGSMITH_ENDPOINT"] = os.getenv(
            "LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"
        )
        os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY", "")
        os.environ["LANGSMITH_PROJECT"] = os.getenv(
            "LANGSMITH_PROJECT", "malaria-rag-system"
        )

        print(
            f"[LangSmith] [OK] Initialized for project: {os.getenv('LANGSMITH_PROJECT')}"
        )
        return True
    except Exception as e:
        print(f"[LangSmith] [X] Failed to initialize: {str(e)}")
        return False


def log_query_start(query: str, country: Optional[str], top_k: int):
    """Log start of query"""
    print(f"[LangSmith] Query started: {query[:50]}...")
    print(f"  Country: {country or 'All'}")
    print(f"  Top-K: {top_k}")
    print(f"  Time: {datetime.now().isoformat()}")


def log_retrieval_results(num_chunks: int, time_ms: float, sections: list):
    """Log retrieval metrics"""
    print(f"[LangSmith] Retrieval complete: {num_chunks} chunks in {time_ms:.2f}ms")
    print(f"  Sections: {sections[:5]}")
    if num_chunks > 0:
        print(f"  Avg/chunk: {time_ms / num_chunks:.2f}ms")
    else:
        print("  No chunks")


def log_llm_generation(answer: str, context_len: int, time_ms: float):
    """Log LLM generation metrics"""
    print(f"[LangSmith] LLM generation: {time_ms:.2f}ms")
    print(f"  Context length: {context_len} chars")
    print(f"  Answer length: {len(answer)} chars")
    print(f"  Answer preview: {answer[:100]}...")


def log_query_complete(
    query: str,
    country: Optional[str],
    top_k: int,
    chunks_retrieved: int,
    is_insufficient: bool,
    total_time_ms: float,
    answer_length: int,
):
    """Log complete query metrics"""
    print(f"\n[LangSmith] Query Complete:")
    print(f"  Query: {query[:60]}...")
    print(f"  Country: {country or 'All'}")
    print(f"  Top-K: {top_k}")
    print(f"  Chunks: {chunks_retrieved}")
    print(f"  Insufficient Evidence: {is_insufficient}")
    print(f"  Total Latency: {total_time_ms:.2f}ms")
    print(f"  Answer Length: {answer_length} chars")
    print(f"  Completed: {datetime.now().isoformat()}\n")


def test_langsmith():
    """Test LangSmith integration"""
    print("\n" + "=" * 60)
    print("LangSmith Integration Test")
    print("=" * 60 + "\n")

    api_key = os.getenv("LANGSMITH_API_KEY", "")
    project = os.getenv("LANGSMITH_PROJECT", "")
    tracing = os.getenv("LANGCHAIN_TRACING_V2", "false")

    if not api_key:
        print("[X] LANGSMITH_API_KEY not set in .env")
        return False

    if not project:
        print("[X] LANGSMITH_PROJECT not set in .env")
        return False

    print(f"[OK] API Key: {api_key[:10]}...{api_key[-10:]}")
    print(f"[OK] Project: {project}")
    print(f"[OK] Tracing: {'Enabled' if tracing == 'true' else 'Disabled'}")

    if init_langsmith():
        print("\n[OK] LangSmith ready!")
        print("  All queries will be traced automatically")
        print("  View at: https://smith.langchain.com/")
    else:
        print("\n[X] LangSmith failed to initialize")

    print("=" * 60 + "\n")
    return True


if __name__ == "__main__":
    test_langsmith()
