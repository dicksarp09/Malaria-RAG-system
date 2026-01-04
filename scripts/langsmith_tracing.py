"""
LangSmith Tracing Module for Malaria RAG System
Provides debugging and monitoring for RAG queries
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime

from langchain.callbacks.tracers import LangChainTracer
from langchain_community.callbacks import get_openai_callback
from langsmith import Client


class RAGTracer:
    """Handles LangSmith tracing for RAG operations"""

    def __init__(self):
        self.enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"

        if self.enabled:
            self.client = Client(api_key=os.getenv("LANGCHAIN_API_KEY"))
            self.tracer = LangChainTracer(
                project_name=os.getenv("LANGCHAIN_PROJECT", "malaria-rag-system")
            )
            print(
                f"[LangSmith] Tracing enabled for project: {os.getenv('LANGCHAIN_PROJECT')}"
            )
        else:
            self.client = None
            self.tracer = None
            print("[LangSmith] Tracing disabled (set LANGCHAIN_TRACING_V2=true)")

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
        """Log a RAG query to LangSmith"""

        if not self.enabled or not self.client:
            return None

        try:
            run_data = {
                "query": query,
                "country_filter": country or "All",
                "top_k": top_k,
                "chunks_retrieved": chunks_retrieved,
                "is_insufficient_evidence": is_insufficient,
                "latency_ms": latency_ms,
                "answer_length": len(answer),
                "timestamp": datetime.now().isoformat(),
            }

            run_id = self.client.create_run(
                name="rag_query",
                inputs={"query": query, "country": country, "top_k": top_k},
                outputs={
                    "answer": answer or "",
                    "chunks_retrieved": chunks_retrieved,
                    "is_insufficient_evidence": is_insufficient,
                },
                run_type="chain",
                metadata=run_data,
            )

            print(f"[LangSmith] Query logged: {query[:50]}... (ID: {run_id})")
            return run_id

        except Exception as e:
            print(f"[LangSmith] Failed to log query: {str(e)}")
            return None

    def log_retrieval(self, query: str, chunks: list, retrieval_time_ms: float):
        """Log retrieval metrics to LangSmith"""

        if not self.enabled:
            return

        try:
            self.client.create_run(
                name="hybrid_retrieval",
                inputs={"query": query},
                outputs={
                    "chunks_retrieved": len(chunks),
                    "retrieval_time_ms": retrieval_time_ms,
                    "avg_final_score": sum(c.get("final_score", 0) for c in chunks)
                    / len(chunks)
                    if chunks
                    else 0,
                    "sections": [
                        c.get("payload", {}).get("section", "unknown")
                        for c in chunks[:5]
                    ],
                },
                run_type="retriever",
                metadata={"alpha": 0.7, "beta": 0.3, "model": "all-MiniLM-L6-v2"},
            )

            print(
                f"[LangSmith] Retrieval logged: {len(chunks)} chunks in {retrieval_time_ms:.2f}ms"
            )

        except Exception as e:
            print(f"[LangSmith] Failed to log retrieval: {str(e)}")

    def log_llm_call(
        self, query: str, context: str, answer: str, llm_latency_ms: float
    ):
        """Log LLM generation to LangSmith"""

        if not self.enabled:
            return

        try:
            self.client.create_run(
                name="llm_generation",
                inputs={
                    "query": query,
                    "context_length": len(context),
                    "context_preview": context[:200] + "...",
                },
                outputs={
                    "answer": answer,
                    "answer_length": len(answer),
                    "llm_latency_ms": llm_latency_ms,
                },
                run_type="llm",
                metadata={
                    "model": "llama-3.3-70b-versatile",
                    "provider": "Groq",
                    "temperature": 0.1,
                    "max_tokens": 1024,
                },
            )

            print(f"[LangSmith] LLM call logged: {llm_latency_ms:.2f}ms")

        except Exception as e:
            print(f"[LangSmith] Failed to log LLM: {str(e)}")


def test_langsmith_connection():
    """Test if LangSmith is properly configured"""

    print("\n=== Testing LangSmith Connection ===\n")

    try:
        from dotenv import load_dotenv

        load_dotenv()

        api_key = os.getenv("LANGCHAIN_API_KEY")
        project = os.getenv("LANGCHAIN_PROJECT")
        tracing = os.getenv("LANGCHAIN_TRACING_V2", "false")

        print(f"API Key: {'✓ Configured' if api_key else '✗ Missing'}")
        print(f"Project: {project if project else '✗ Not set'}")
        print(f"Tracing: {'✓ Enabled' if tracing.lower() == 'true' else '✗ Disabled'}")

        if tracing.lower() == "true" and api_key:
            tracer = RAGTracer()

            test_query = "Test query for LangSmith"
            run_id = tracer.log_query(
                query=test_query,
                country="Nigeria",
                top_k=5,
                chunks_retrieved=3,
                is_insufficient=False,
                latency_ms=150.5,
                answer="Test answer from RAG system",
            )

            if run_id:
                print(f"\n✓ Successfully logged test run to LangSmith")
                print(f"  Run ID: {run_id}")
                print(f"  View at: https://smith.langchain.com/")
            else:
                print("\n✗ Failed to log to LangSmith")
        else:
            print("\n✗ LangSmith not enabled")

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")

    print("\n=== End Test ===\n")


if __name__ == "__main__":
    test_langsmith_connection()
