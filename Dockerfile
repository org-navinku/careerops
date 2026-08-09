FROM python:3.14-slim

RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY careerops.html .
COPY backend.py .

RUN useradd -m -u 1000 careerops \
    && chown -R careerops:careerops /app

USER careerops

EXPOSE 5001 8000

HEALTHCHECK \
    --interval=30s \
    --timeout=10s \
    --start-period=5s \
    --retries=3 \
    CMD curl -f http://localhost:5001/api/health || exit 1

CMD ["sh", "-c", "python3 backend.py & python3 -m http.server 8000"]