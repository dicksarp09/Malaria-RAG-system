import sqlite3
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np
import math
from collections import Counter


def get_db_path():
    return Path(__file__).parent.parent / "data" / "metadata" / "documents.db"


def get_qdrant_client():
    client = QdrantClient(path=str(Path(__file__).parent.parent / "data" / "qdrant_collection"))
    return client


def log_event(conn, document_id: str, level: str, message: str):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO ingestion_logs (document_id, level, message) VALUES (?, ?, ?)",
        (document_id, level, message),
    )
    conn.commit()


class BM25Index:
    def __init__(self):
        self.documents = {}
        self.idf = {}
        self.doc_lengths = {}
        self.avg_doc_length = 0
        self.k1 = 1.5
        self.b = 0.75

    def build_index(self, chunks: List[Tuple]):
        self.documents = {}
        term_doc_freq = {}

        for chunk_id, text in chunks:
            tokens = text.lower().split()
            self.documents[chunk_id] = tokens
            self.doc_lengths[chunk_id] = len(tokens)

            term_counts = Counter(tokens)
            for term in term_counts:
                if term not in term_doc_freq:
                    term_doc_freq[term] = 0
                term_doc_freq[term] += 1

        if self.doc_lengths:
            self.avg_doc_length = sum(self.doc_lengths.values()) / len(self.doc_lengths)

        N = len(self.documents)

        for term, doc_freq in term_doc_freq.items():
            self.idf[term] = math.log((N - doc_freq + 0.5) / (doc_freq + 0.5) + 1)

    def score(self, chunk_id: str, query: str) -> float:
        if chunk_id not in self.documents:
            return 0.0

        tokens = self.documents[chunk_id]
        query_tokens = query.lower().split()

        score = 0.0
        doc_length = self.doc_lengths[chunk_id]

        for term in query_tokens:
            if term in tokens and term in self.idf:
                term_freq = tokens.count(term)
                numerator = self.idf[term] * term_freq * (self.k1 + 1)
                denominator = term_freq + self.k1 * (
                    1 - self.b + self.b * (doc_length / self.avg_doc_length)
                )
                score += numerator / denominator

        return score

    def batch_score(self, query: str, chunk_ids: List[str]) -> Dict[str, float]:
        scores = {}
        for chunk_id in chunk_ids:
            scores[chunk_id] = self.score(chunk_id, query)
        return scores


class HybridRetriever:
    def __init__(self):
        self.qdrant_client = get_qdrant_client()
        self.semantic_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.bm25_index = BM25Index()
        self.collection_name = "malaria_chunks"
        self.alpha = 0.7
        self.beta = 0.3

        self.section_boosts = {
            "results": 0.3,
            "methods": 0.2,
            "discussion": 0.1,
            "abstract": 0.05,
            "tables": 0.0,
            "full_text": 0.0,
        }

        self._initialize()

    def _initialize(self):
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT chunk_id, text FROM chunks")
        chunks = cursor.fetchall()
        conn.close()

        if chunks:
            self.bm25_index.build_index(chunks)

    def _apply_filters(self, country: Optional[str] = None) -> Optional[Filter]:
        conditions = []

        if country:
            conditions.append(FieldCondition(key="country", match=MatchValue(value=country)))

        return Filter(must=conditions) if conditions else None

    def _semantic_search(
        self, query_embedding: np.ndarray, filters: Optional[Filter], limit: int
    ) -> List[Dict]:
        search_results = self.qdrant_client.query_points(
            collection_name=self.collection_name,
            query=query_embedding.tolist(),
            query_filter=filters,
            limit=limit * 2,
            with_payload=True,
        ).points

        results = []
        for result in search_results:
            results.append(
                {
                    "chunk_id": result.id,
                    "score": result.score if hasattr(result, "score") else 0.0,
                    "payload": result.payload,
                }
            )

        return results

    def _normalize_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        if not scores:
            return {}

        max_score = max(scores.values())
        if max_score == 0:
            return {k: 0.0 for k in scores}

        return {k: v / max_score for k, v in scores.items()}

    def _apply_section_boosts(self, results: List[Dict]) -> List[Dict]:
        for result in results:
            section = result.get("payload", {}).get("section", "")
            boost = self.section_boosts.get(section, 0.0)
            result["section_boost"] = boost
            result["final_score"] = result["final_score"] + boost

        return results

    def retrieve(
        self,
        query: str,
        country: Optional[str] = None,
        K: int = 10,
        log_retrieval: bool = True,
    ) -> List[Dict]:
        conn = sqlite3.connect(get_db_path())

        try:
            query_embedding = self.semantic_model.encode(query)

            filters = self._apply_filters(country)

            semantic_results = self._semantic_search(query_embedding, filters, K * 2)

            if not semantic_results:
                if log_retrieval:
                    filter_info = f"country={country}" if country else "none"
                    message = f'Query: "{query[:100]}...", Filters: {filter_info}, Results: 0'
                    log_event(conn, None, "WARNING", message)
                conn.close()
                return []

            chunk_ids = [r["chunk_id"] for r in semantic_results]

            chunk_ids = [r["chunk_id"] for r in semantic_results]

            bm25_scores = self.bm25_index.batch_score(query, chunk_ids)
            semantic_scores = {r["chunk_id"]: r["score"] for r in semantic_results}

            normalized_semantic = self._normalize_scores(semantic_scores)
            normalized_bm25 = self._normalize_scores(bm25_scores)

            results = []
            for r in semantic_results:
                chunk_id = r["chunk_id"]
                semantic_score = normalized_semantic.get(chunk_id, 0.0)
                bm25_score = normalized_bm25.get(chunk_id, 0.0)

                final_score = self.alpha * semantic_score + self.beta * bm25_score

                result = {
                    "chunk_id": chunk_id,
                    "semantic_score": semantic_score,
                    "bm25_score": bm25_score,
                    "final_score": final_score,
                    "payload": r["payload"],
                }
                results.append(result)

            results.sort(key=lambda x: x["final_score"], reverse=True)

            results = self._apply_section_boosts(results)

            results.sort(key=lambda x: x["final_score"], reverse=True)

            results = results[:K]

            if log_retrieval:
                filter_info = f"country={country}" if country else "none"
                scores_info = ", ".join(
                    [
                        f"semantic={r['semantic_score']:.3f}, "
                        f"bm25={r['bm25_score']:.3f}, "
                        f"final={r['final_score']:.3f}"
                        for r in results[:3]
                    ]
                )

                message = (
                    f'Query: "{query[:100]}...", '
                    f"Filters: {filter_info}, "
                    f"Retrieved: {len(results)}/{K} chunks, "
                    f"Top scores: [{scores_info}]"
                )

                log_event(
                    conn,
                    results[0]["payload"]["document_id"] if results else None,
                    "INFO",
                    message,
                )

            return results

        except Exception as e:
            if log_retrieval:
                log_event(
                    conn,
                    None,
                    "ERROR",
                    f'Retrieval failed for query "{query[:100]}...": {str(e)}',
                )
            conn.close()
            return []


def retrieve(query: str, country: Optional[str] = None, K: int = 10) -> List[Dict]:
    retriever = HybridRetriever()
    return retriever.retrieve(query, country=country, K=K)


if __name__ == "__main__":
    import json

    print("Testing Hybrid Retrieval System")
    print("=" * 60)

    queries = [
        "malaria treatment effectiveness in Ghana",
        "childhood malaria prevention strategies",
        "drug resistance in Nigeria malaria cases",
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        print("-" * 60)

        results = retrieve(query, country=None, K=5)

        if results:
            print(f"Retrieved {len(results)} chunks:\n")

            for i, result in enumerate(results[:3], 1):
                print(f"{i}. Chunk ID: {result['chunk_id']}")
                print(f"   Section: {result['payload'].get('section', 'N/A')}")
                print(f"   Country: {result['payload'].get('country', 'N/A')}")
                print(f"   Semantic Score: {result['semantic_score']:.4f}")
                print(f"   BM25 Score: {result['bm25_score']:.4f}")
                print(f"   Section Boost: {result.get('section_boost', 0.0):.2f}")
                print(f"   Final Score: {result['final_score']:.4f}")
                print(f"   Char Count: {result['payload'].get('char_count', 'N/A')}")
                print()
        else:
            print("No results found.\n")

    print("\nTesting with country filter")
    print("=" * 60)

    query = "malaria treatment outcomes"
    country = "Nigeria"
    print(f"\nQuery: {query}")
    print(f"Country Filter: {country}")
    print("-" * 60)

    results = retrieve(query, country=country, K=3)

    if results:
        print(f"Retrieved {len(results)} chunks:\n")

        for i, result in enumerate(results, 1):
            print(f"{i}. Chunk ID: {result['chunk_id']}")
            print(f"   Section: {result['payload'].get('section', 'N/A')}")
            print(f"   Country: {result['payload'].get('country', 'N/A')}")
            print(f"   Final Score: {result['final_score']:.4f}")
            print()
    else:
        print("No results found.\n")

    print("Hybrid retrieval test completed!")
