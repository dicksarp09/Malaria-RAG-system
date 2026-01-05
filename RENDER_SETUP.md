# Render Deployment Configuration

## What's Been Set Up

### 1. render.yaml
- Configures web service with Docker
- Sets up persistent disk (10GB) at /app/data
- Configures health check at /health
- Defines environment variables (GROQ_API_KEY, etc.)

### 2. Backend Files Updated
- **Dockerfile**: Updated to initialize storage before starting app
- **init_storage.py**: New script to create database and Qdrant collection on first run
- **hybrid_retrieval.py**: Updated Qdrant path to match deployment structure
- **.env.example**: Template for required environment variables
- **.dockerignore**: Optimizes Docker build by excluding unnecessary files

### 3. Deployment Documentation
- **BACKEND_DEPLOYMENT.md**: Complete deployment guide with troubleshooting

## Quick Start

1. Push code to GitHub
2. Connect Render to your repository
3. Create new Web Service with these settings:
   - Environment: Docker
   - Docker Context: ./backend
   - Dockerfile: ./backend/Dockerfile
   - Mount disk at /app/data (10GB)
4. Add GROQ_API_KEY environment variable
5. Deploy!

## Key Points

- **Persistent Storage**: 10GB disk mounted at /app/data for DB and Qdrant
- **Health Check**: /health endpoint available
- **Port**: 8000
- **Auto-initialization**: Database and Qdrant collection created on first run
- **Cold Starts**: ~30-60s on free tier (expected behavior)

## Next Steps

1. Deploy backend to Render following BACKEND_DEPLOYMENT.md
2. Get the backend URL (e.g., https://malaria-rag-backend-xxxx.onrender.com)
3. Update frontend API configuration with new backend URL
4. Deploy frontend to Vercel
