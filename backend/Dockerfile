# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Copy scripts from parent directory
COPY ../scripts/ /app/scripts/

# Create data directories
RUN mkdir -p /app/data/metadata /app/data/qdrant_collection

# Expose port
EXPOSE 8000

# Run initialization and start application
CMD ["sh", "-c", "python init_storage.py && uvicorn main:app --host 0.0.0.0 --port 8000"]
