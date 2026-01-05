# Backend Deployment to Render

## Prerequisites

- Render account (free tier available)
- GitHub repository with code pushed
- Groq API key

## Setup Instructions

### 1. Push Code to GitHub

Ensure your code is pushed to GitHub:
```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

### 2. Connect Render to GitHub

1. Go to [render.com](https://render.com)
2. Sign up/login
3. Go to Dashboard → New Service
4. Select "Web Service"
5. Connect your GitHub repository
6. Select the "RAG project" repository

### 3. Configure Service

In Render service settings:

**Basic Settings:**
- Name: `malaria-rag-backend`
- Environment: `Docker`
- Branch: `main`

**Advanced Settings:**
- Docker Context: `./backend`
- Dockerfile Path: `./backend/Dockerfile`
- Instance Type: `Free` (or Starter $7/mo for better performance)

**Environment Variables:**
Add these environment variables:
```
GROQ_API_KEY=your_actual_api_key_here
PYTHONUNBUFFERED=1
PORT=8000
LANGCHAIN_TRACING_V2=false
LANGCHAIN_PROJECT=malaria-rag
```

**Persistent Disk:**
- Mount Path: `/app/data`
- Disk Name: `data`
- Size: `10 GB` (minimum, adjust based on your needs)

**Health Check:**
- Path: `/health`

### 4. Deploy

Click "Create Web Service" to deploy. Render will:
1. Build the Docker image
2. Initialize the database and Qdrant storage
3. Start the FastAPI server
4. Run health checks

### 5. Verify Deployment

Once deployed, you can:
- Check logs in Render dashboard
- Test health endpoint: `https://your-app.onrender.com/health`
- Test root endpoint: `https://your-app.onrender.com/`

### 6. Get API URL

Your backend will be available at:
```
https://malaria-rag-backend-xxxx.onrender.com
```

Note this URL for frontend deployment.

## Troubleshooting

### Build Fails
- Check Dockerfile path is correct: `./backend/Dockerfile`
- Verify requirements.txt has all dependencies
- Check Render build logs

### Health Check Fails
- Verify PORT is set to `8000`
- Check if app is binding to `0.0.0.0`
- Review application logs

### Database Issues
- Ensure persistent disk is mounted at `/app/data`
- Check disk size (at least 10GB recommended)
- Verify init_storage.py runs successfully

### Qdrant Issues
- Ensure Qdrant collection is created during init
- Check vector dimensions match (384 for all-MiniLM-L6-v2)
- Verify Qdrant storage path: `/app/data/qdrant_collection`

## Important Notes

1. **Persistent Storage**: Render persistent disks are required for database and Qdrant storage
2. **Cold Starts**: Free tier has cold starts (30-60s) after inactivity
3. **Environment Variables**: Never commit `.env` files - use Render's environment variables
4. **Data Ingestion**: You'll need to run ingestion scripts separately or deploy a worker
5. **CORS**: Backend allows all origins - consider restricting for production

## Next Steps

After backend is deployed:
1. Note the backend URL
2. Update frontend API configuration
3. Deploy frontend to Vercel
4. Test end-to-end functionality
