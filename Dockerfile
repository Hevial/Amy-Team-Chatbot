# ==============================================================================
# Stage 1: Frontend Builder (React/Vite)
# ==============================================================================
FROM node:22-alpine AS frontend-builder
WORKDIR /app

# Install dependencies first for better layer caching
COPY frontend-web/package.json frontend-web/package-lock.json* ./
RUN npm install

# Copy source and build
COPY frontend-web/ ./
RUN npm run build


# ==============================================================================
# Stage 2: Backend Builder (Python)
# ==============================================================================
FROM python:3.11-slim AS backend-builder
WORKDIR /app

# Install build dependencies required by ChromaDB and others
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies into a local directory
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ==============================================================================
# Stage 3: Final Runtime Image (Unified Container for Cloud Run)
# ==============================================================================
FROM python:3.11-slim
WORKDIR /app

# Copy the compiled python dependencies
COPY --from=backend-builder /install /usr/local

# Copy backend application source code
COPY src/ ./src/
COPY data/ ./data/
COPY scripts/ ./scripts/
COPY chroma_db/ ./chroma_db/

# Copy the compiled React static files
COPY --from=frontend-builder /app/dist ./frontend-web/dist

# Create a non-root user for security (Standard for GCP Cloud Run)
RUN useradd -m -r appuser && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

USER appuser

# Set environment variables for production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose the port for Cloud Run / Docker Compose
EXPOSE 8080

# Start the FastAPI application via Uvicorn (serves API + React static files)
CMD sh -c "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}"
