"""
Publish user activity events to GCP Pub/Sub. A subscriber (Cloud Run) writes to BigQuery.
If PUBSUB_ACTIVITY_TOPIC is not set, all publish calls are no-ops.
"""
import os
import json
import logging
from typing import Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Lazy client to avoid import/credentials errors at startup
_pubsub_client = None
_topic_path = None
_disabled = None


def _get_topic() -> Optional[str]:
    global _disabled
    if _disabled is True:
        return None
    topic = os.getenv("PUBSUB_ACTIVITY_TOPIC", "").strip()
    if not topic:
        _disabled = True
        return None
    return topic


def _get_pubsub_credentials():
    """
    Build credentials that include the Pub/Sub scope. The same key used for Play may be
    loaded elsewhere with only androidpublisher scope, causing ACCESS_TOKEN_SCOPE_INSUFFICIENT.
    We explicitly request pubsub scope here.
    """
    from google.oauth2 import service_account
    from utils.env_json import parse_json_from_env

    scopes = ["https://www.googleapis.com/auth/pubsub"]
    key = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY") or os.getenv("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON", "")
    if not key or not str(key).strip():
        return None
    key = key.strip()
    # Inline JSON
    info = parse_json_from_env(key)
    if info and isinstance(info, dict):
        return service_account.Credentials.from_service_account_info(info, scopes=scopes)
    # File path
    if os.path.isfile(key):
        return service_account.Credentials.from_service_account_file(key, scopes=scopes)
    return None


def _get_client():
    """Lazy init Pub/Sub publisher client with credentials that have Pub/Sub scope."""
    global _pubsub_client
    if _pubsub_client is not None:
        return _pubsub_client
    topic = _get_topic()
    if not topic:
        return None
    try:
        from google.cloud import pubsub_v1

        project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT_ID", "").strip()
        if not project:
            from utils.env_json import parse_json_from_env
            key = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY") or os.getenv("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON", "")
            if key:
                info = parse_json_from_env(key.strip()) if isinstance(key, str) else None
                if info and isinstance(info, dict):
                    project = info.get("project_id", "")
            if not project:
                logger.warning("Activity: GOOGLE_CLOUD_PROJECT / GCP_PROJECT_ID not set; Pub/Sub publish may fail")

        creds = _get_pubsub_credentials()
        if creds is not None:
            publisher = pubsub_v1.PublisherClient(credentials=creds)
        else:
            publisher = pubsub_v1.PublisherClient()
        _pubsub_client = publisher
        return _pubsub_client
    except Exception as e:
        logger.warning("Activity: could not create Pub/Sub client: %s", e)
        return None


def _publish_sync(payload: dict) -> bool:
    """Publish one message to the activity topic. Runs in thread to avoid blocking."""
    topic_name = _get_topic()
    if not topic_name:
        return False
    client = _get_client()
    if not client:
        return False
    project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT_ID", "").strip()
    if not project:
        from utils.env_json import parse_json_from_env
        key = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY", "")
        if key and isinstance(key, str):
            info = parse_json_from_env(key.strip())
            if info and isinstance(info, dict):
                project = info.get("project_id", "")
    if not project:
        logger.warning("Activity: project id missing, skipping publish")
        return False
    # topic_name can be "topic-name" or "projects/PROJECT/topics/topic-name"
    if topic_name.startswith("projects/"):
        topic_path = topic_name
    else:
        topic_path = f"projects/{project}/topics/{topic_name}"
    try:
        data = json.dumps(payload).encode("utf-8")
        future = client.publish(topic_path, data)
        future.result(timeout=5)
        return True
    except Exception as e:
        logger.warning("Activity: Pub/Sub publish failed: %s", e)
        return False


def publish_activity(
    action: str,
    *,
    user_id: Optional[int] = None,
    user_phone: Optional[str] = None,
    user_name: Optional[str] = None,
    path: Optional[str] = None,
    method: Optional[str] = None,
    status_code: Optional[int] = None,
    duration_ms: Optional[float] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    metadata: Optional[dict] = None,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    error_type: Optional[str] = None,
    error_message: Optional[str] = None,
    stack_trace: Optional[str] = None,
) -> bool:
    """
    Publish an activity event to Pub/Sub. Fire-and-forget; does not block.
    Call from middleware (api_request) or from routes (e.g. podcast_generated, credits_purchased).
    """
    payload = {
        "action": action,
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    if user_id is not None:
        payload["user_id"] = user_id
    if user_phone is not None:
        payload["user_phone"] = str(user_phone)
    if user_name is not None:
        payload["user_name"] = (str(user_name)[:200] if len(str(user_name)) > 200 else str(user_name))
    if path is not None:
        payload["path"] = path
    if method is not None:
        payload["method"] = method
    if status_code is not None:
        payload["status_code"] = status_code
    if duration_ms is not None:
        payload["duration_ms"] = round(duration_ms, 2)
    if resource_type is not None:
        payload["resource_type"] = resource_type
    if resource_id is not None:
        payload["resource_id"] = str(resource_id)
    if metadata is not None:
        payload["metadata"] = metadata
    if ip is not None:
        payload["ip"] = ip
    if user_agent is not None:
        payload["user_agent"] = (user_agent[:500] if len(user_agent or "") > 500 else user_agent)
    if error_type is not None:
        payload["error_type"] = (str(error_type)[:200] if len(str(error_type)) > 200 else str(error_type))
    if error_message is not None:
        msg = str(error_message)
        payload["error_message"] = msg[:8000] if len(msg) > 8000 else msg
    if stack_trace is not None:
        st = str(stack_trace)
        # Keep message sizes bounded for Pub/Sub payload.
        payload["stack_trace"] = st[:40000] if len(st) > 40000 else st

    try:
        return _publish_sync(payload)
    except Exception as e:
        logger.warning("Activity: publish_activity failed: %s", e)
        return False
