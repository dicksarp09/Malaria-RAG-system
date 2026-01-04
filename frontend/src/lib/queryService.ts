import { QueryRequest, QueryResponse, ChunkMetadata } from './api';
import { QueryResult, Country, Citation } from '../types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export const api = {
  async post(url: string, data: any) {
    const response = await fetch(`${API_BASE_URL}${url}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }
    return response.json();
  }
};

export const transformResponse = (response: QueryResponse, query: string, country: Country, topK: number): QueryResult => {
  const citations: Citation[] = response.retrieved_chunks.map((chunk, idx) => ({
    id: `cit-${idx}`,
    sourceId: chunk.chunk_id,
    section: chunk.section as Citation['section'],
    content: chunk.text || '',
    relevanceScore: chunk.final_score,
  }));

  return {
    answer: response.answer,
    citations,
    hasSufficientEvidence: !response.is_insufficient_evidence,
    timestamp: new Date().toISOString(),
    metadata: {
      query,
      country,
      topK,
    },
  };
};

export const runResearchQuery = async (
  query: string,
  country: Country,
  topK: number
): Promise<QueryResult> => {
  const request: QueryRequest = {
    user_query: query,
    country: country === 'All' ? undefined : country,
    top_k: topK,
  };

  const response: QueryResponse = await api.post('/query', request);
  return transformResponse(response, query, country, topK);
};
