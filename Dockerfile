# Multi-stage build for CareerOps
# Stage 1: Python runtime with dependencies
FROM python:3.14-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final image
FROM python:3.14-slim

# Install system dependencies (minimal for runtime)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python packages from base stage
COPY --from=base /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=base /usr/local/bin /usr/local/bin

# Copy application files
COPY careerops.html .
COPY backend.py .
COPY requirements.txt .

# Create non-root user for security
RUN useradd -m -u 1000 careerops && chown -R careerops:careerops /app
USER careerops

# Expose ports
# 5001: Backend API
# 8000: Frontend HTTP server
EXPOSE 5001 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/api/health || exit 1

# Start both backend and frontend
CMD ["sh", "-c", "python3 backend.py & python3 -m http.server 8000"]
