# ── Stage 1: builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build tools needed by some packages (e.g. grpcio wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies into a local prefix so we can copy them cleanly
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --prefix=/install --no-cache-dir -r requirements.txt


# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Non-root user for security
RUN groupadd --gid 1001 appgroup \
 && useradd  --uid 1001 --gid appgroup --no-create-home appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY main.py .
COPY app/ ./app/

# Cloud Run injects PORT env var; default to 8080 for local docker run
ENV PORT=8080
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Drop to non-root
USER appuser

# EXPOSE is informational; Cloud Run uses PORT env var
EXPOSE 8080

# Bind to 0.0.0.0:$PORT as required by Cloud Run
CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1"]
