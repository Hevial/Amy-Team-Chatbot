# Stage 1: Builder
# We use a builder stage to compile C-extensions (like hnswlib for ChromaDB)
# and install dependencies cleanly without bringing build tools into the final image.
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies required by ChromaDB and others
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies into a local directory
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Stage 2: Runtime
# This is the final, minimal image that gets deployed to Cloud Run
FROM python:3.11-slim

WORKDIR /app

# Copy the compiled dependencies from the builder stage
COPY --from=builder /install /usr/local

# Copy application source code
COPY src/ ./src/
COPY frontend/ ./frontend/
COPY data/ ./data/

# Set environment variables for production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose the port for Cloud Run / Docker Compose
EXPOSE 8080

# Start the FastAPI application via Uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
