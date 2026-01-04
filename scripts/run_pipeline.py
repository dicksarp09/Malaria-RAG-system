import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import subprocess
import sys
import json


class NodeStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    SKIPPED = "skipped"


@dataclass
class NodeResult:
    node_name: str
    status: NodeStatus
    data: Any
    error: Optional[str]
    execution_time: float
    timestamp: datetime


class PipelineOrchestrator:
    def __init__(self):
        self.nodes: Dict[str, Callable] = {}
        self.edges: Dict[str, List[str]] = {}
        self.db_path = (
            Path(__file__).parent.parent / "data" / "metadata" / "documents.db"
        )
        self.logs: List[Dict] = []

    def register_node(self, name: str, func: Callable):
        """Register a pipeline node."""
        self.nodes[name] = func

    def register_edge(self, from_node: str, to_node: str):
        """Register an edge between nodes."""
        if from_node not in self.edges:
            self.edges[from_node] = []
        self.edges[from_node].append(to_node)

    def log_execution(
        self,
        node_name: str,
        status: NodeStatus,
        data: Any = None,
        error: str = None,
        execution_time: float = 0.0,
        document_id: str = None,
        query_id: str = None,
    ):
        """Log node execution."""
        log_entry = {
            "node_name": node_name,
            "status": status.value,
            "timestamp": datetime.now().isoformat(),
            "execution_time": execution_time,
            "document_id": document_id,
            "query_id": query_id,
            "data": str(data)[:500] if data else None,
            "error": error,
        }
        self.logs.append(log_entry)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO ingestion_logs (document_id, level, message)
            VALUES (?, ?, ?)
            """,
            (
                document_id or query_id or "orchestrator",
                "INFO" if status == NodeStatus.SUCCESS else "ERROR",
                f"Pipeline Node: {node_name}, Status: {status.value}, Time: {execution_time:.2f}s"
                + (f", Error: {error}" if error else ""),
            ),
        )
        conn.commit()
        conn.close()

    def run_node(self, node_name: str, **kwargs) -> NodeResult:
        """Execute a single node with retries."""
        if node_name not in self.nodes:
            return NodeResult(
                node_name=node_name,
                status=NodeStatus.FAILURE,
                data=None,
                error=f"Node {node_name} not registered",
                execution_time=0.0,
                timestamp=datetime.now(),
            )

        start_time = datetime.now()
        func = self.nodes[node_name]

        for attempt in range(3):
            try:
                result = func(**kwargs)
                execution_time = (datetime.now() - start_time).total_seconds()

                self.log_execution(
                    node_name=node_name,
                    status=NodeStatus.SUCCESS,
                    data=result,
                    execution_time=execution_time,
                    document_id=kwargs.get("document_id"),
                    query_id=kwargs.get("query_id"),
                )

                return NodeResult(
                    node_name=node_name,
                    status=NodeStatus.SUCCESS,
                    data=result,
                    error=None,
                    execution_time=execution_time,
                    timestamp=datetime.now(),
                )

            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                error_msg = str(e)

                if attempt < 2:
                    continue

                self.log_execution(
                    node_name=node_name,
                    status=NodeStatus.FAILURE,
                    error=error_msg,
                    execution_time=execution_time,
                    document_id=kwargs.get("document_id"),
                    query_id=kwargs.get("query_id"),
                )

                return NodeResult(
                    node_name=node_name,
                    status=NodeStatus.FAILURE,
                    data=None,
                    error=error_msg,
                    execution_time=execution_time,
                    timestamp=datetime.now(),
                )

    def execute_pipeline(self, start_node: str, **kwargs):
        """Execute pipeline from start node."""
        results = {}
        visited = set()
        queue = [start_node]

        while queue:
            node_name = queue.pop(0)

            if node_name in visited:
                continue

            if node_name not in self.nodes:
                continue

            self.log_execution(
                node_name=node_name,
                status=NodeStatus.RUNNING,
                data=f"Executing node {node_name}",
                document_id=kwargs.get("document_id"),
                query_id=kwargs.get("query_id"),
            )

            result = self.run_node(node_name, **kwargs)
            results[node_name] = result

            if result.status == NodeStatus.FAILURE:
                self.log_execution(
                    node_name=node_name,
                    status=NodeStatus.FAILURE,
                    data=f"Pipeline stopped at {node_name}",
                    document_id=kwargs.get("document_id"),
                    query_id=kwargs.get("query_id"),
                )
                break

            visited.add(node_name)

            if node_name in self.edges:
                queue.extend(self.edges[node_name])

        return results


def node_pdf_ingestion(pdfs_dir: Path, **kwargs) -> Dict:
    """PDF Ingestion Node."""
    import sys

    sys.path.append(str(Path(__file__).parent.parent))

    result = subprocess.run(
        ["python", "scripts/ingest_pdfs.py"],
        cwd=str(Path(__file__).parent.parent),
        capture_output=True,
        text=True,
        timeout=600,
    )

    if result.returncode != 0:
        raise Exception(f"Ingestion failed: {result.stderr}")

    return {"stdout": result.stdout, "stderr": result.stderr}


def node_text_extraction(**kwargs) -> Dict:
    """Text Extraction & Country Attribution Node."""
    import sys

    sys.path.append(str(Path(__file__).parent.parent))

    result = subprocess.run(
        ["python", "scripts/text_extractability_check.py"],
        cwd=str(Path(__file__).parent.parent),
        capture_output=True,
        text=True,
        timeout=600,
    )

    if result.returncode != 0:
        raise Exception(f"Text extraction failed: {result.stderr}")

    return {"stdout": result.stdout, "stderr": result.stderr}


def node_country_attribution(**kwargs) -> Dict:
    """Country Attribution Node."""
    import sys

    sys.path.append(str(Path(__file__).parent.parent))

    result = subprocess.run(
        ["python", "scripts/country_attribution.py"],
        cwd=str(Path(__file__).parent.parent),
        capture_output=True,
        text=True,
        timeout=600,
    )

    if result.returncode != 0:
        raise Exception(f"Country attribution failed: {result.stderr}")

    return {"stdout": result.stdout, "stderr": result.stderr}


def node_chunking(**kwargs) -> Dict:
    """Chunking Node."""
    import sys

    sys.path.append(str(Path(__file__).parent.parent))

    result = subprocess.run(
        ["python", "scripts/chunk_documents.py"],
        cwd=str(Path(__file__).parent.parent),
        capture_output=True,
        text=True,
        timeout=1800,
    )

    if result.returncode != 0:
        raise Exception(f"Chunking failed: {result.stderr}")

    return {"stdout": result.stdout, "stderr": result.stderr}


def node_embeddings(**kwargs) -> Dict:
    """Embeddings Node."""
    import sys

    sys.path.append(str(Path(__file__).parent.parent))

    result = subprocess.run(
        ["python", "scripts/embed_chunks.py"],
        cwd=str(Path(__file__).parent.parent),
        capture_output=True,
        text=True,
        timeout=1800,
    )

    if result.returncode != 0:
        raise Exception(f"Embeddings failed: {result.stderr}")

    return {"stdout": result.stdout, "stderr": result.stderr}


def node_hybrid_retrieval(
    query: str, country: Optional[str] = None, top_k: int = 10, **kwargs
) -> Dict:
    """Hybrid Retrieval Node."""
    import sys

    sys.path.append(str(Path(__file__).parent.parent))

    from scripts.hybrid_retrieval import HybridRetriever

    retriever = HybridRetriever()
    chunks = retriever.retrieve(
        query=query, country=country, K=top_k, log_retrieval=False
    )

    return {
        "query": query,
        "chunks": chunks,
        "chunks_retrieved": len(chunks),
        "country": country,
        "top_k": top_k,
    }


def node_llm_rag(
    query: str, country: Optional[str] = None, top_k: int = 10, **kwargs
) -> Dict:
    """LLM RAG Query Node."""
    import sys

    sys.path.append(str(Path(__file__).parent.parent))

    from scripts.llm_rag_query import rag_query

    response = rag_query(
        user_query=query, country=country, top_k=top_k, log_to_db=False
    )

    return response


def node_evaluation(**kwargs) -> Dict:
    """Evaluation Node."""
    conn = sqlite3.connect(
        str(Path(__file__).parent.parent / "data" / "metadata" / "documents.db")
    )
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM ingestion_logs WHERE message LIKE 'LLM Query:%'"
    )
    total_queries = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM ingestion_logs WHERE message LIKE '%Refusal: True%'"
    )
    insufficient_queries = cursor.fetchone()[0]

    refusal_rate = (insufficient_queries / total_queries) if total_queries > 0 else 0

    cursor.close()

    return {
        "total_queries": total_queries,
        "insufficient_queries": insufficient_queries,
        "refusal_rate": refusal_rate,
        "sufficient_queries": total_queries - insufficient_queries,
    }


def build_ingestion_pipeline(orchestrator: PipelineOrchestrator):
    """Build the ingestion pipeline graph."""
    orchestrator.register_node("pdf_ingestion", node_pdf_ingestion)
    orchestrator.register_node("text_extraction", node_text_extraction)
    orchestrator.register_node("country_attribution", node_country_attribution)
    orchestrator.register_node("chunking", node_chunking)
    orchestrator.register_node("embeddings", node_embeddings)

    orchestrator.register_edge("pdf_ingestion", "text_extraction")
    orchestrator.register_edge("pdf_ingestion", "country_attribution")
    orchestrator.register_edge("text_extraction", "chunking")
    orchestrator.register_edge("country_attribution", "chunking")
    orchestrator.register_edge("chunking", "embeddings")


def build_query_pipeline(orchestrator: PipelineOrchestrator):
    """Build the query pipeline graph."""
    orchestrator.register_node("hybrid_retrieval", node_hybrid_retrieval)
    orchestrator.register_node("llm_rag", node_llm_rag)

    orchestrator.register_edge("hybrid_retrieval", "llm_rag")


def build_evaluation_pipeline(orchestrator: PipelineOrchestrator):
    """Build the evaluation pipeline graph."""
    orchestrator.register_node("evaluation", node_evaluation)


def run_ingestion_pipeline():
    """Run the complete ingestion pipeline."""
    orchestrator = PipelineOrchestrator()
    build_ingestion_pipeline(orchestrator)

    pdfs_dir = Path(__file__).parent.parent / "data" / "raw" / "pfds"

    results = orchestrator.execute_pipeline(
        start_node="pdf_ingestion", pdfs_dir=pdfs_dir
    )

    print("=" * 80)
    print("Ingestion Pipeline Results")
    print("=" * 80)

    for node_name, result in results.items():
        status_symbol = "✓" if result.status == NodeStatus.SUCCESS else "✗"
        print(f"{status_symbol} {node_name}: {result.status.value}")
        if result.error:
            print(f"   Error: {result.error}")
        print(f"   Time: {result.execution_time:.2f}s")

    return results


def run_query_pipeline(query: str, country: Optional[str] = None, top_k: int = 10):
    """Run the query pipeline."""
    orchestrator = PipelineOrchestrator()
    build_query_pipeline(orchestrator)

    results = orchestrator.execute_pipeline(
        start_node="hybrid_retrieval",
        query=query,
        country=country,
        top_k=top_k,
        query_id=f"query_{datetime.now().strftime('%Y%m%d%H%M%S')}",
    )

    print("=" * 80)
    print("Query Pipeline Results")
    print("=" * 80)
    print(f"Query: {query}")
    print(f"Country: {country or 'All'}")
    print(f"Top K: {top_k}")

    retrieval_result = results.get("hybrid_retrieval")
    if retrieval_result and retrieval_result.status == NodeStatus.SUCCESS:
        print(f"\nChunks Retrieved: {retrieval_result.data.get('chunks_retrieved', 0)}")

    llm_result = results.get("llm_rag")
    if llm_result and llm_result.status == NodeStatus.SUCCESS:
        answer = llm_result.data.get("answer", "")
        is_insufficient = llm_result.data.get("is_insufficient_evidence", False)

        print(f"\nAnswer:")
        print("-" * 80)
        if is_insufficient:
            print("⚠️  INSUFFICIENT EVIDENCE")
            print("-" * 80)
        print(answer)
        print("-" * 80)

    print("\n" + "=" * 80)

    return results


def run_evaluation_pipeline():
    """Run the evaluation pipeline."""
    orchestrator = PipelineOrchestrator()
    build_evaluation_pipeline(orchestrator)

    results = orchestrator.execute_pipeline(start_node="evaluation")

    print("=" * 80)
    print("Evaluation Pipeline Results")
    print("=" * 80)

    eval_result = results.get("evaluation")
    if eval_result and eval_result.status == NodeStatus.SUCCESS:
        data = eval_result.data
        print(f"Total Queries: {data.get('total_queries', 0)}")
        print(f"Sufficient Evidence: {data.get('sufficient_queries', 0)}")
        print(f"Insufficient Evidence: {data.get('insufficient_queries', 0)}")
        print(f"Refusal Rate: {data.get('refusal_rate', 0):.2%}")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Malaria RAG Pipeline Orchestrator")
    parser.add_argument(
        "--pipeline",
        choices=["ingestion", "query", "evaluation"],
        required=True,
        help="Pipeline to run",
    )
    parser.add_argument("--query", type=str, help="Query for query pipeline")
    parser.add_argument("--country", type=str, help="Country filter")
    parser.add_argument("--top-k", type=int, default=10, help="Top K results")

    args = parser.parse_args()

    if args.pipeline == "ingestion":
        run_ingestion_pipeline()
    elif args.pipeline == "query":
        if not args.query:
            print("Error: --query is required for query pipeline")
            sys.exit(1)
        run_query_pipeline(args.query, args.country, args.top_k)
    elif args.pipeline == "evaluation":
        run_evaluation_pipeline()
