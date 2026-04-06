# Stage 1: dependency layer
FROM python:3.11-slim AS deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: application layer
FROM python:3.11-slim AS app
WORKDIR /app

# Copy installed packages from deps stage
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create data directory for audit logs and precedents
RUN mkdir -p /app/data

# Non-root user for security
RUN useradd -m -u 1001 swarm && chown -R swarm:swarm /app
USER swarm

# Environment defaults (override at runtime)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SWARM_CHECKPOINTING_BACKEND=memory

ENTRYPOINT ["python", "run_swarm.py"]
CMD ["--help"]
