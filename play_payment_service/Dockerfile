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

COPY play_payment_service/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend/ /app/
COPY play_payment_service /app/play_payment_service

RUN chmod +x /app/play_payment_service/start.sh

# Fail the image build if the intentionally-trimmed payment-service context is
# missing a transitive Python module. Without this check Cloud Build succeeds,
# but Cloud Run only discovers the problem when Uvicorn starts the revision.
RUN JWT_SECRET=payment-service-build-smoke-test \
    python -c "import play_payment_service.main"

EXPOSE 8080

CMD ["/app/play_payment_service/start.sh"]
