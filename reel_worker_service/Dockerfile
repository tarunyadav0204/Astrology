FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /tmp/backend-requirements.txt
RUN pip install --no-cache-dir -r /tmp/backend-requirements.txt

COPY backend/ /app/
COPY reel_worker_service /app/reel_worker_service
COPY assets/logo.png /app/assets/logo.png

RUN chmod +x /app/reel_worker_service/start.sh

EXPOSE 8080

CMD ["/app/reel_worker_service/start.sh"]
