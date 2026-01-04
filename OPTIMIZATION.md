# Systematic Optimization Procedure for Malaria RAG System

## Phase 1: Baseline & Measurement

1. **Profile each component**
   - Add timing to each step:
     - Retrieval time (embedding + search)
     - LLM generation time
     - Database query time
     - Total latency

2. **Track current metrics**
   - Average retrieval time
   - Average LLM time
   - Context length per query
   - Token usage per query

## Phase 2: Quick Wins (Immediate Impact)

### A. Reduce LLM Context
- **Send only essential chunks**
- Use summary of chunks instead of full text
- Limit context to top 3-5 chunks
- Truncate long chunks to 500 chars

### B. Adjust Retrieval Parameters
- **In query endpoint**
- Reduce `top_k` from 10 → 5
- Increase retrieval score threshold
- Use country filter to reduce search space

### C. Add Caching
- **Cache frequent queries**
- Redis for query-answer pairs
- Cache identical queries for 24h
- Use query hash as cache key

## Phase 3: Retrieval Optimization

### A. Better Embedding Model
- **Current**: `all-MiniLM-L6-v2` (fast, okay quality)
- **Faster**: `bge-small-en` (similar speed, better retrieval)
- **Higher quality**: `bge-large-en` (slower, better precision)

### B. Optimize Hybrid Search
- **Tune alpha/beta weights**
- Semantic: 70%, BM25: 30% (current)
- Test 50/50, 60/40
- Use A/B testing to find optimal

### C. Pre-computation
- Pre-compute embeddings for all chunks (done ✓)
- Cache BM25 scores (already done ✓)
- Add section-based filtering

## Phase 4: LLM Optimization

### A. Smaller/Faster Models
- **Groq models by speed (fastest first)**:
  1. `llama-3.1-8b-instant` (~50ms, cheaper)
  2. `llama-3.1-8b` (~100ms, cheaper)
  3. `llama-3.3-70b-versatile` (~200ms, current)

### B. Model Routing
- **Use smaller model for simple queries**:
- If query length < 50 chars → 8b model
- If context < 2000 chars → 8b model
- Otherwise → 70b model

### C. Reduce Token Usage
- **Optimize prompt**:
- Current: ~150 tokens system prompt
- Target: ~50 tokens
- Use shorter instructions
- Remove redundant text

## Phase 5: Infrastructure Optimization

### A. Database Optimization
- **SQLite**:
- Add indexes on `chunk_id`, `document_id`
- Use prepared statements (already done ✓)
- Connection pooling

### B. Vector Search Optimization
- **Qdrant**:
- Use HNSW index (already configured ✓)
- Adjust `ef_search` parameter (speed vs precision)
- Consider quantization for faster search

### C. Async Operations
- **Parallelize independent tasks**:
- Fetch chunk texts in parallel
- Compute embeddings async
- Stream LLM responses

## Phase 6: Cost Optimization

### A. Monitor Token Usage
- **Track tokens per query**:
- Input tokens: context length / 4
- Output tokens: answer length / 4
- Set alert if > 1000 tokens/query

### B. Groq Cost Analysis
- **Current**: `llama-3.3-70b-versatile`
  - Input: ~$0.60 per million tokens
  - Output: ~$0.60 per million tokens
- **Optimized**: `llama-3.1-8b`
  - Input: ~$0.06 per million tokens (10x cheaper!)
  - Output: ~$0.06 per million tokens (10x cheaper!)

### C. Reduce Unnecessary Queries
- Add rate limiting
- Filter invalid queries upfront
- Combine similar queries

## Optimization Roadmap (Priority Order)

| Priority | Change | Expected Impact | Effort |
| :--- | :--- | :--- | :--- |
| 1 | Reduce `top_k` (10→5) | -30% latency | 5 min |
| 2 | Switch to 8b model for simple queries | -50% cost, -40% latency | 1 hour |
| 3 | Add query caching | -60% latency for repeated queries | 2 hours |
| 4 | Optimize system prompt | -20% tokens | 30 min |
| 5 | Implement model routing | -30% average cost | 2 hours |
| 6 | Parallel chunk fetching | -20% latency | 1 hour |

## Target Metrics

**Current → Target**
- **P50 latency**: 70ms → 30ms
- **P99 latency**: 930ms → 500ms
- **Cost/query**: $0.001 → $0.0001
- **Error rate**: 0% → 0%

*Start with Phase 1 (profiling).*
