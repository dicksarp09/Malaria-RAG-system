# Malaria RAG System - Backend + Frontend

A production-ready RAG system for querying malaria research papers from Ghana and Nigeria. This system is designed for clinical precision, evidence-backed synthesis, and strict adherence to provided source material.

## 🏗️ Architecture

The system uses a graph-based orchestration to manage the complete RAG workflow, ensuring modularity and idempotency.

- **Frontend (Next.js 14)**: A "Stream & Sidebar" UI/UX designed for clinical research.
- **Backend (FastAPI)**: RESTful API that integrates core RAG scripts and provides evaluation metrics.
- **Vector Store (Qdrant)**: High-performance vector database for semantic search.
- **Metadata Store (SQLite)**: Core audit trail and document metadata management.
- **Monitoring Stack**: Prometheus for metrics collection and Grafana for visualization.
- **Orchestration**: Graph-based pipeline managing ingestion and query flows.

## 🧬 Core Pipelines

### 1. Ingestion & Preprocessing
The ingestion pipeline ensures that only high-quality, relevant documents are admitted to the corpus:
- **PDF Registration**: Detects and deduplicates files using SHA256 checksums.
- **Text Qualification**: Extracts text using `PyMuPDF` and evaluates extraction quality (min 3000 chars, low empty page ratio).
- **Country Attribution**: Identifies if study locations are Ghana, Nigeria, or both (Ghana|Nigeria) with confidence scoring.
- **Section-Aware Chunking**: Splits text based on scientific sections (Abstract, Methods, Results, Discussion) with optimized chunk sizes.
- **Embeddings**: Generates 384-d vectors using `all-MiniLM-L6-v2`.

### 2. Retrieval & Synthesis
- **Hybrid Retrieval**: Combines semantic search (70%) with BM25 keyword matching (30%).
- **Section Boosts**: Prioritizes evidence from high-impact sections:
  - Results (+0.3)
  - Methods (+0.2)
  - Discussion (+0.1)
  - Abstract (+0.05)
- **Clinical RAG**: LLM (LLaMA-3.3-70b-Versatile via Groq) generates answers strictly based on context.
- **Refusal Logic**: Returns "INSUFFICIENT EVIDENCE" if the corpus cannot directly answer the query.

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- Groq API Key (for LLM generation)

### Backend Setup
1. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
2. **Initialize Database & Vectors**:
   ```bash
   python scripts/create_db.py
   python scripts/run_pipeline.py --pipeline ingestion
   ```
3. **Run the API**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup
1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```
2. **Configure Environment**:
   ```bash
   echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
   ```
3. **Run Dev Server**:
   ```bash
    npm run dev
    ```

### Docker Setup (Recommended)

The easiest way to run the entire system with monitoring:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/dicksarp09/Malaria-RAG-system.git
   cd Malaria-RAG-system
   ```

2. **Set up environment**:
   ```bash
   cp backend/.env.example backend/.env
   ```
   Edit `backend/.env` and add your Groq API key:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

3. **Start all services**:
   ```bash
   docker-compose up -d
   ```

   This will start:
   - Backend API: `http://localhost:8000`
   - Frontend: `http://localhost:3000`
   - Prometheus: `http://localhost:9090`
   - Grafana: `http://localhost:3000` (admin/admin)

4. **Initialize the database** (first time only):
   ```bash
   docker-compose exec backend python scripts/create_db.py
   ```

5. **View metrics**:
   - Prometheus UI: http://localhost:9090
   - Grafana Dashboard: http://localhost:3000 (Login: admin/admin)
   - Backend metrics: http://localhost:8000/metrics

6. **Stop services**:
   ```bash
   docker-compose down
   ```

## 📊 Monitoring & Evaluation

### Application Metrics (Prometheus + Grafana)

The system exposes Prometheus metrics at `/metrics` endpoint:

- **Query Metrics**:
  - `rag_queries_total` - Total number of queries (labeled by country and status)
  - `rag_query_duration_seconds` - Query duration histogram
  - `rag_retrieved_chunks` - Number of chunks retrieved per query
  - `rag_llm_latency_seconds` - LLM response latency histogram

- **Dashboards**:
  - Pre-configured Grafana dashboard at `/var/lib/grafana/dashboards/rag-dashboard.json`
  - Includes query rate, latency percentiles, and retrieval statistics
  - Auto-refreshes every 5 seconds

### Observability

- **LangSmith Tracing**: Full observability of query latency, retrieval quality, and LLM behavior.
- **Evaluation Dashboard**: Accessible via `GET /evaluation/metrics`, providing refusal rates and average chunks per query.
- **Audit Logs**: Comprehensive logging in the SQLite database accessible via `GET /logs`.

## 📂 Project Structure

```text
malaria-rag/
├── scripts/              # Core pipeline: Ingest, Chunk, Embed, Retrieve
├── backend/              # FastAPI application with modular routers
│   ├── routers/          # Query, Ingestion, Chunks, Logs, Evaluation
│   └── models/           # Pydantic schemas
├── frontend/             # Next.js 14 application
│   ├── src/components/   # Sidebar, InputBar, EvidenceBlock
│   └── src/app/          # Stream architecture
├── data/                 # SQLite metadata and Qdrant local storage
├── prometheus/           # Prometheus configuration
│   └── prometheus.yml    # Scrape configuration
├── grafana/              # Grafana configuration
│   ├── provisioning/     # Datasources and dashboard provisioning
│   └── dashboards/       # Pre-configured dashboards
├── docker-compose.yml    # Docker orchestration
├── OPTIMIZATION.md       # Roadmap for performance & cost tuning
└── README.md             # This file
```

## 📜 License
Proprietary - Medical RAG System for Malaria Research
