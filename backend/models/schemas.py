from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class IngestRequest(BaseModel):
    files: list[str]


class IngestResponse(BaseModel):
    success: bool
    message: str
    documents_processed: int
    duplicates_skipped: int
    errors: int


class QueryRequest(BaseModel):
    user_query: str
    country: Optional[str] = None
    disease: Optional[str] = None
    year: Optional[int] = None
    top_k: int = 10


class ChunkMetadata(BaseModel):
    chunk_id: str
    document_id: str
    section: str
    text: str
    char_count: int
    final_score: float
    semantic_score: float
    bm25_score: float
    country: Optional[str] = None
    section_boost: Optional[float] = None


class QueryResponse(BaseModel):
    query: str
    answer: str
    retrieved_chunks: List[ChunkMetadata]
    top_chunk_ids: List[str]
    chunks_retrieved: int
    is_insufficient_evidence: bool
    filters_applied: Dict[str, Any]


class RebuildRequest(BaseModel):
    confirm: bool = False


class RebuildResponse(BaseModel):
    success: bool
    message: str
    chunks_rebuilt: int
    embeddings_recreated: int


class LogEntry(BaseModel):
    log_id: int
    document_id: Optional[str]
    level: str
    message: str
    created_at: datetime


class LogsResponse(BaseModel):
    total_logs: int
    logs: List[LogEntry]


class EvaluationMetrics(BaseModel):
    total_queries: int
    sufficient_evidence_queries: int
    insufficient_evidence_queries: int
    refusal_rate: float
    avg_chunks_per_query: float
    top_sections: List[Dict[str, Any]]
