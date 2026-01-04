# Malaria RAG Pipeline Orchestration

A graph-based orchestration system for managing the complete malaria RAG workflow.

## Architecture

### Nodes

The pipeline consists of modular nodes that can be executed independently:

1. **PDF Ingestion Node** - Uploads and deduplicates PDFs
2. **Text Extraction Node** - Extracts and qualifies text
3. **Country Attribution Node** - Detects Ghana/Nigeria from documents
4. **Chunking Node** - Creates section-aware chunks
5. **Embeddings Node** - Generates and stores embeddings
6. **Hybrid Retrieval Node** - Retrieves chunks with semantic + BM25 + section boosts
7. **LLM RAG Query Node** - Generates evidence-backed answers
8. **Evaluation Node** - Calculates system metrics

### Pipeline Graphs

#### Ingestion Pipeline
```
PDF Ingestion → Text Extraction → Chunking → Embeddings
                ↓
          Country Attribution
```

#### Query Pipeline
```
Hybrid Retrieval → LLM RAG Query → Frontend Response
                ↓
          Evaluation (async)
```

## Usage

### Run Complete Ingestion Pipeline

```bash
# Ingest all PDFs, extract text, attribute countries, chunk, and embed
python scripts/run_pipeline.py --pipeline ingestion
```

### Run Query Pipeline

```bash
# Query the RAG system
python scripts/run_pipeline.py --pipeline query \
    --query "What prevention methods are used for malaria?" \
    --country "Ghana" \
    --top-k 10
```

### Run Evaluation Pipeline

```bash
# Calculate system metrics
python scripts/run_pipeline.py --pipeline evaluation
```

## Features

### Idempotency
- Each node can be re-run without creating duplicates
- Checksum-based deduplication for PDFs
- Qdrant idempotency for embeddings

### Failure Handling
- Transient failures are retried 1-2 times
- Permanent failures stop the pipeline and log errors
- Each node's failure is isolated (doesn't affect other nodes)

### Logging
- Every node execution is logged to `ingestion_logs` table
- Logs include: node_name, status, execution_time, document_id/query_id
- Timestamped for audit trail
- ERROR level for failures, INFO for success

### Branching & Refusal
- Documents failing ingestion → branch to ingestion_logs
- Retrieval with insufficient chunks → LLM returns "INSUFFICIENT EVIDENCE"
- Low confidence answers → logged as WARNING
- Rejection at any step → logged as ERROR

### Execution Policy
1. **Input Validation** - Nodes validate inputs before processing
2. **Retry Logic** - Transient failures retried up to 2 times
3. **Timeout Handling** - Nodes have appropriate timeouts (5-30 minutes)
4. **Error Propagation** - Failures stop pipeline immediately
5. **Modularity** - Each node can run independently

## Node Details

### PDF Ingestion Node
- **Input**: PDFs directory
- **Output**: Accepted/rejected documents, ingestion logs
- **Timeout**: 10 minutes
- **Deduplication**: SHA256 checksums
- **Idempotent**: Skips already-registered PDFs

### Text Extraction Node
- **Input**: Accepted documents
- **Output**: Text-extracted documents
- **Thresholds**:
  - Min characters: 3000
  - Min avg chars/page: 300
  - Max empty page ratio: 0.2
- **Idempotent**: Only processes `pending` documents

### Country Attribution Node
- **Input**: Text-extracted documents
- **Output**: Documents with country labels
- **Countries Detected**: Ghana, Nigeria, Ghana|Nigeria
- **Confidence Scoring**: 0.0-1.0
- **Idempotent**: Only processes documents without country

### Chunking Node
- **Input**: Country-attributed documents
- **Output**: Section-aware chunks
- **Sections**: abstract, methods, results, discussion, tables, full_text
- **Chunk Sizes**:
  - Abstract: 500-800 chars
  - Methods/Results: 1000-1500 chars
  - Discussion: 800-1200 chars
  - Tables: 200-2000 chars
  - Full text: 1000-1500 chars
- **Idempotent**: Skips documents with existing chunks

### Embeddings Node
- **Input**: Chunks
- **Output**: Embeddings in Qdrant
- **Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Distance Metric**: Cosine similarity
- **Idempotent**: Skips chunks with existing embeddings

### Hybrid Retrieval Node
- **Input**: Query + filters (country, top_k)
- **Output**: Top-K chunks with scores
- **Scoring**: 70% semantic + 30% BM25
- **Section Boosts**:
  - Results: +0.3
  - Methods: +0.2
  - Discussion: +0.1
  - Abstract: +0.05
  - Tables/Full text: 0.0
- **Filtering**: Country, disease, year (optional)

### LLM RAG Query Node
- **Input**: Top-K chunks + query
- **Output**: Evidence-backed answer or "INSUFFICIENT EVIDENCE"
- **Model**: Groq LLaMA-3.3-70b-Versatile
- **Citations**: [Document ID: xxx] [Section: xxx]
- **Safety**: No clinical diagnoses or prescriptions

### Evaluation Node
- **Input**: Query logs
- **Output**: System metrics
- **Metrics**:
  - Total queries
  - Sufficient evidence queries
  - Insufficient evidence queries
  - Refusal rate
  - Average chunks per query
  - Top sections retrieved

## Orchestration API

### Programmatic Usage

```python
from scripts.run_pipeline import PipelineOrchestrator, run_query_pipeline

# Run query programmatically
results = run_query_pipeline(
    query="What are malaria treatment strategies?",
    country="Ghana",
    top_k=5
)

# Access individual node results
retrieval_result = results["hybrid_retrieval"]
llm_result = results["llm_rag"]

print(f"Retrieval status: {retrieval_result.status.value}")
print(f"LLM status: {llm_result.status.value}")
```

### Custom Pipeline

```python
from scripts.run_pipeline import PipelineOrchestrator, build_query_pipeline

# Create orchestrator
orchestrator = PipelineOrchestrator()

# Build custom pipeline
build_query_pipeline(orchestrator)

# Execute custom workflow
results = orchestrator.execute_pipeline(
    start_node="hybrid_retrieval",
    query="Custom query",
    top_k=15
)
```

## Orchestration Rules

### Dependency Management
- Nodes execute in dependency order
- Parallel execution for independent nodes
- Sequential execution for dependent nodes

### State Management
- Each node receives input parameters
- Each node returns structured result
- State flows through edges

### Error Handling
- Node failures stop pipeline at that point
- Upstream nodes continue independently
- All errors logged for debugging

### Idempotency Rules
1. Check for existing work before executing
2. Use checksums or IDs to detect duplicates
3. Only process new or modified data
4. Maintain consistent state across runs

## Monitoring & Observability

### Pipeline Logs
```bash
# View all pipeline executions
sqlite3 data/metadata/documents.db \
  "SELECT * FROM ingestion_logs WHERE message LIKE 'Pipeline Node:%' ORDER BY created_at DESC"
```

### Execution Metrics
```bash
# View node execution times
sqlite3 data/metadata/documents.db \
  "SELECT message FROM ingestion_logs WHERE message LIKE 'Pipeline Node:%' ORDER BY created_at DESC LIMIT 10"
```

### Failure Analysis
```bash
# View failed nodes
sqlite3 data/metadata/documents.db \
  "SELECT * FROM ingestion_logs WHERE level = 'ERROR' ORDER BY created_at DESC"
```

## Production Deployment

### Running as Daemon
```bash
# Ingestion daemon (runs every 24 hours)
while true; do
  python scripts/run_pipeline.py --pipeline ingestion
  sleep 86400
done
```

### Running with Systemd
```ini
# /etc/systemd/system/malaria-rag.service
[Unit]
Description=Malaria RAG Pipeline
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/RAG project
ExecStart=/usr/bin/python3 scripts/run_pipeline.py --pipeline query
Restart=always

[Install]
WantedBy=multi-user.target
```

### Scheduled Queries
```bash
# Run evaluation weekly (cron)
0 0 * * 0 python /path/to/RAG project/scripts/run_pipeline.py --pipeline evaluation
```

## Integration with Backend API

The orchestrator can be triggered by the FastAPI backend:

```python
# backend/routers/orchestration.py
from scripts.run_pipeline import run_query_pipeline, run_ingestion_pipeline

@router.post("/ingestion")
async def trigger_ingestion():
    results = run_ingestion_pipeline()
    return {"status": "success", "results": results}

@router.post("/query-pipeline")
async def trigger_query_pipeline(request: QueryRequest):
    results = run_query_pipeline(
        query=request.user_query,
        country=request.country,
        top_k=request.top_k
    )
    return results
```

## Security Considerations

1. **API Orchestration Only** - User-facing actions handled by backend
2. **Input Validation** - All inputs validated before processing
3. **Error Messages** - Sensitive information not exposed
4. **Logging** - No passwords or API keys in logs
5. **File System** - PDFs only from allowed directory

## Troubleshooting

### Pipeline Stuck
```bash
# Check for running processes
ps aux | grep python

# Kill stuck processes
pkill -9 -f ingest_pdfs
```

### Memory Issues
```bash
# Monitor memory usage
top -p python

# Reduce batch sizes if needed
# Modify scripts to process in smaller batches
```

### Database Locks
```bash
# Check for locks
lsof data/metadata/documents.db

# Release locks (last resort)
rm -f data/metadata/documents.db-wal data/metadata/documents.db-shm
```

## Performance Optimization

### Parallel Processing
```python
# Process multiple documents in parallel
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = []
    for doc in documents:
        future = executor.submit(process_document, doc)
        futures.append(future)

    for future in futures:
        result = future.result()
```

### Caching
```python
# Cache Qdrant client
class QdrantClientSingleton:
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = QdrantClient(path="...")
        return cls._instance
```

### Batch Processing
```python
# Process chunks in batches
batch_size = 100
for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i+batch_size]
    process_batch(batch)
```

## Extending the Pipeline

### Adding New Nodes

```python
def node_custom_processing(**kwargs) -> Dict:
    """Custom node implementation."""
    # Process data
    return {"status": "success", "data": result}

# Register in orchestrator
orchestrator.register_node("custom", node_custom_processing)
orchestrator.register_edge("custom", "next_node")
```

### Conditional Branching

```python
# Branch based on results
if result.data.get("confidence", 0) < 0.5:
    orchestrator.execute_pipeline(
        start_node="log_refusal",
        reason="Low confidence"
    )
else:
    orchestrator.execute_pipeline(
        start_node="next_step",
        data=result.data
    )
```

## License

Proprietary - Medical RAG System for Malaria Research
