# Backend Dockerfile for Vagrantfile Generator
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Move shared seed data to a separate location (not shadowed by PVC mount)
# This allows the entrypoint to copy it to /app/data/shared on first run
RUN mkdir -p /app/seed-data && \
    if [ -d /app/data/shared ]; then \
    mv /app/data/shared /app/seed-data/shared; \
    fi

# Create data directory for persistence (will be mounted as PVC in k8s)
RUN mkdir -p /app/data

# Copy and set up entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Create a non-root user
RUN addgroup --gid 1001 appgroup \
    && adduser --uid 1001 --ingroup appgroup --disabled-login --no-create-home appuser --gecos "" \
    && chown -R appuser:appgroup /app /app/seed-data

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use entrypoint to seed data, then run the application
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "src.main:app", "-b", "0.0.0.0:8000", "--workers", "4"]
