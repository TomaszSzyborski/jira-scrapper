FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY jira_analyzer/ ./jira_analyzer/
COPY web/ ./web/

# Create data directories
RUN mkdir -p /app/data/cache /app/data/reports

# Set working directory to web
WORKDIR /app/web

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run with Gunicorn + Uvicorn workers for production
# For development, override with: docker-compose run --rm jira-analyzer uvicorn app:app --reload
CMD ["gunicorn", "app:app", "-c", "gunicorn.conf.py"]
