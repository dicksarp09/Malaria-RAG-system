import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface QueryRequest {
  user_query: string;
  country?: string;
  disease?: string;
  year?: number;
  top_k?: number;
}

export interface QueryResponse {
  query: string;
  answer: string;
  retrieved_chunks: ChunkMetadata[];
  top_chunk_ids: string[];
  chunks_retrieved: number;
  is_insufficient_evidence: boolean;
  filters_applied: {
    country?: string;
    top_k: number;
  };
}

export interface ChunkMetadata {
  chunk_id: string;
  document_id: string;
  section: string;
  char_count: number;
  final_score: number;
  semantic_score: number;
  bm25_score: number;
  country?: string;
  section_boost?: number;
}

export interface EvaluationMetrics {
  total_queries: number;
  sufficient_evidence_queries: number;
  insufficient_evidence_queries: number;
  refusal_rate: number;
  avg_chunks_per_query: number;
  top_sections: { section: string; count: number }[];
}

export const queryRAG = async (request: QueryRequest): Promise<QueryResponse> => {
  const response = await api.post('/query', request);
  return response.data;
};

export const getEvaluationMetrics = async (): Promise<EvaluationMetrics> => {
  const response = await api.get('/evaluation/metrics');
  return response.data;
};

export const getLogs = async (level?: string, limit = 100, offset = 0) => {
  const response = await api.get('/logs', {
    params: { level, limit, offset }
  });
  return response.data;
};
