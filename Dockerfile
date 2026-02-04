# STAGE 1: Build Frontend
FROM node:20-slim AS frontend-builder

WORKDIR /app/src/web

# Copy frontend definitions
COPY src/web/package.json src/web/package-lock.json* ./
RUN npm ci

# Copy frontend source
COPY src/web/ .

# Build (Output goes to /app/dist/web via vite config)
RUN npm run build


# STAGE 2: Runtime Environment
FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src/core

# Install system dependencies (if any needed for Stanza/Torch)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU first (to keep image size small)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install Project dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Core and API code
COPY src/core /app/src/core
COPY src/api /app/src/api
COPY config.yaml /app/config.yaml

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/dist/web /app/dist/web

# Create models directory (for persistence)
RUN mkdir -p /app/models && chmod 777 /app/models

# Expose port 7860 (Hugging Face Spaces default)
EXPOSE 7860

# Run the application
CMD ["uvicorn", "src.api.app.main:app", "--host", "0.0.0.0", "--port", "7860"]