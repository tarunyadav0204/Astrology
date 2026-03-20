"""
Cloud Run service: receives Pub/Sub push messages (user activity events) and inserts into BigQuery.
Set PUBSUB push subscription URL to this service's /push endpoint.
"""
import os
import json
import base64
import logging
from datetime import datetime, timezone
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# BigQuery
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT_ID")
DATASET_ID = os.getenv("BIGQUERY_DATASET_ID", "activity")
TABLE_ID = os.getenv("BIGQUERY_TABLE_ID", "user_activity")
FULL_TABLE = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}" if PROJECT_ID else None


def _parse_iso_ts(s: str):
    """Parse ISO timestamp string to BigQuery TIMESTAMP."""
    if not s:
        return None
    try:
        # BigQuery expects UTC
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f UTC")
    except Exception:
        return None


def _row_from_payload(msg_id: str, payload: dict) -> dict:
    """Map activity JSON payload to BigQuery row."""
    created_at = payload.get("created_at")
    if isinstance(created_at, str):
        ts = _parse_iso_ts(created_at)
    else:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f UTC")

    metadata = payload.get("metadata")
    if isinstance(metadata, dict):
        metadata = json.dumps(metadata)

    return {
        "event_id": msg_id,
        "user_id": payload.get("user_id"),
        "user_phone": payload.get("user_phone"),
        "user_name": payload.get("user_name"),
        "action": payload.get("action") or "unknown",
        "path": payload.get("path"),
        "method": payload.get("method"),
        "status_code": payload.get("status_code"),
        "duration_ms": payload.get("duration_ms"),
        "resource_type": payload.get("resource_type"),
        "resource_id": payload.get("resource_id"),
        "metadata": metadata,
        "error_type": payload.get("error_type"),
        "error_message": payload.get("error_message"),
        "stack_trace": payload.get("stack_trace"),
        "ip": payload.get("ip"),
        "user_agent": payload.get("user_agent"),
        "created_at": ts,
    }


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "activity-subscriber"}), 200


@app.route("/push", methods=["POST"])
def push():
    """
    Pub/Sub push endpoint. Body: { "message": { "data": "<base64>", "messageId": "..." }, "subscription": "..." }
    """
    if not FULL_TABLE:
        logger.error("BIGQUERY: PROJECT/DATASET not configured")
        return jsonify({"error": "not configured"}), 500

    envelope = request.get_json(silent=True)
    if not envelope or "message" not in envelope:
        logger.warning("Push: invalid body (no message)")
        return jsonify({"error": "invalid body"}), 400

    message = envelope["message"]
    raw_data = message.get("data")
    msg_id = message.get("messageId", "")

    if not raw_data:
        logger.warning("Push: empty message data")
        return "", 200

    try:
        data = base64.b64decode(raw_data).decode("utf-8")
        payload = json.loads(data)
    except Exception as e:
        logger.warning("Push: decode/parse failed: %s", e)
        return "", 200

    row = _row_from_payload(msg_id, payload)

    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=PROJECT_ID)
        errors = client.insert_rows_json(FULL_TABLE, [row])
        if errors:
            logger.warning("BigQuery insert_rows_json errors: %s", errors)
            return jsonify({"error": "insert failed", "details": str(errors)}), 500
    except Exception as e:
        logger.exception("BigQuery insert failed: %s", e)
        return jsonify({"error": str(e)}), 500

    return "", 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
