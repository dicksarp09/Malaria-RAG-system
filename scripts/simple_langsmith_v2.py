"""
Simple LangSmith tracer for RAG system using only langsmith SDK
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from langsmith import Client
from dotenv import load_dotenv

# Load .env from backend directory
env_path = Path(__file__).parent.parent / "backend" / ".env"
load_dotenv(env_path)


class SimpleLangSmith:
    def __init__(self):
        self.enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
        self.client = None

        if self.enabled:
            try:
                api_key = os.getenv("LANGCHAIN_API_KEY")
                project = os.getenv("LANGCHAIN_PROJECT", "malaria-rag-system")

                if not api_key:
                    print("[LangSmith] ERROR: LANGCHAIN_API_KEY not set")
                    self.enabled = False
                    return

                self.client = Client(api_key=api_key)
                print(f"[LangSmith] Connected to project: {project}")
            except Exception as e:
                print(f"[LangSmith] Failed to initialize: {e}")
                self.enabled = False
        else:
            print("[LangSmith] Disabled (set LANGCHAIN_TRACING_V2=true)")

    def log_query(
        self,
        query: str,
        country: Optional[str],
        top_k: int,
        chunks_retrieved: int,
        is_insufficient: bool,
        latency_ms: float,
        answer: str,
    ) -> Optional[str]:
        if not self.enabled or not self.client:
            return None

        try:
            run = self.client.create_run(
                name="rag_query",
                inputs={"query": query, "country": country or "All", "top_k": top_k},
                outputs={
                    "answer": answer[:500] + "..." if len(answer) > 500 else answer,
                    "chunks_retrieved": chunks_retrieved,
                    "is_insufficient_evidence": is_insufficient,
                    "latency_ms": latency_ms,
                },
                run_type="chain",
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "answer_length": len(answer),
                    "country_filter": country or "All",
                },
            )
            print(f"[LangSmith] Run logged: {run[:10]}..." if run else "")
            return run
        except Exception as e:
            print(f"[LangSmith] Failed to log query: {e}")
            return None


tracer = SimpleLangSmith()
