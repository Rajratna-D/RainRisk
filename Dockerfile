# =============================================================================
# RainRisk: Production Multi-Stage Container Image
# Stage 1: Build modern React 19 / Vite client bundle
# Stage 2: Minimalist, hardened Python 3.11 ASGI production runner
# =============================================================================

# --- Stage 1: Frontend Build ---
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Cache package manifests for efficient layer caching
COPY frontend/package*.json ./
RUN npm ci --prefer-offline || npm install

# Build compiled assets into frontend/dist
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Production Python Backend ---
FROM python:3.11-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8008 \
    HOST=0.0.0.0 \
    ENVIRONMENT=production

WORKDIR /app

# Install curl for container health check probes
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python production dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code, models, data, and configurations
COPY . .

# Copy compiled frontend distribution from builder stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Non-root user security hardening
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8008

# Container Healthcheck (polled by Docker engine / Kubernetes / Render)
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8008}/health || exit 1

# Launch ASGI application dynamically binding to cloud provider PORT
CMD ["sh", "-c", "exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8008}"]
