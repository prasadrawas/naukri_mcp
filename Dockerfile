# Production Dockerfile for naukri-mcp (Standalone Repository)
FROM python:3.12-slim

WORKDIR /app

# Install curl for healthcheck probes
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install runtime dependencies directly
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "mcp>=1.0.0" "uvicorn>=0.30.0" "starlette>=0.38.0" "pydantic>=2.0.0" "httpx2>=2.16.0" "pypdf>=4.0.0"

# Copy source repository into /app/naukri_mcp
COPY . /app/naukri_mcp/

# Set PYTHONPATH so python -m naukri_mcp resolves /app/naukri_mcp cleanly without editable install
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Expose standard port for SSE mode (Railway dynamically maps $PORT)
EXPOSE 8000

# Health check probe against /health
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Default command: run in SSE mode for remote HTTP/SSE connections, dynamically respecting $PORT
CMD ["sh", "-c", "python -m naukri_mcp --transport sse --port ${PORT:-8000} --host 0.0.0.0"]
