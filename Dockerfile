# Multi-stage build for production deployment
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code - Updated for unified architecture
COPY apps/ ./apps/
COPY shared/ ./shared/
COPY data/ ./data/
COPY .env .env

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Expose port (for documentation, Cloud Run ignores this)
EXPOSE $PORT

# Run the application
# Updated for unified architecture - Default to word_query_api
# For meal_analysis_api, override with: CMD python -m apps.meal_analysis_api.main
CMD python -m apps.word_query_api.main