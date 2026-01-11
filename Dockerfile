# Use Python 3.11 slim as base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml setup.py MANIFEST.in ./
COPY src/ ./src/

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -e .

# Create data directory for ChromaDB persistence
RUN mkdir -p /data

# Set volume for data persistence
VOLUME ["/data"]

# Expose port (if using HTTP transport in the future)
EXPOSE 8000

# Set default command
ENTRYPOINT ["ucp"]
CMD ["serve"]
