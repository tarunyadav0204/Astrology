# Play Payment Service

Small Cloud Run-targeted service for Google Play purchase verification.

## Purpose

This service allows the main backend to proxy selected users' Google Play credit and
subscription verification traffic to an isolated runtime, controlled by admin settings.

The main backend keeps a **safe fallback**:
- if the service is down / times out / returns 5xx, the existing in-VM code path still runs

## Endpoints

- `GET /`
- `POST /internal/google-play/verify`
- `POST /internal/google-play/subscription/verify`
- `POST /internal/google-play/subscription/sync`

## Required env

- dedicated shared secret:
  - `PLAY_PAYMENT_SERVICE_SHARED_SECRET`
- same Play / DB env that the backend already needs:
  - `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON` or `GOOGLE_SERVICE_ACCOUNT_KEY`
  - DB / secret envs used by the backend

In production, the recommended setup is:
- mount `APP_ENV_FILE` from Secret Manager to `/secrets/app_env/.env`
- inject `PLAY_PAYMENT_SERVICE_SHARED_SECRET` from Secret Manager as an env secret
- keep `min-instances=1` to avoid cold-start latency on payment verification

## Main-backend admin settings

- `play_payment_service_enabled`
- `play_payment_service_user_allowlist`
- `play_payment_service_base_url`

## Local run

From repo root:

```bash
docker build -f play_payment_service/Dockerfile -t play-payment-service .
docker run --rm -p 8080:8080 \
  -e PLAY_PAYMENT_SERVICE_SHARED_SECRET=dev-secret \
  -v "$PWD/backend/.env:/app/backend/.env:ro" \
  play-payment-service
```
