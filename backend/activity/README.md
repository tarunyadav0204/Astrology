# User Activity Logging (Pub/Sub → BigQuery)

All user activity is published to GCP Pub/Sub and written to BigQuery by a small Cloud Run subscriber. This keeps the activity table off SQLite and scales with usage.

## Flow

1. **Backend (FastAPI)**  
   - **Middleware**: Every API request (with optional JWT) is logged as `action=api_request` (path, method, status_code, duration_ms, user_phone from JWT).  
   - **Explicit events**: Key actions call `publish_activity(...)` (e.g. `podcast_generated`, `credits_purchased`).

2. **Pub/Sub**  
   - Messages are published to the topic configured by `PUBSUB_ACTIVITY_TOPIC`.  
   - If the topic is not set, publishing is a no-op.

3. **Subscriber (Cloud Run)**  
   - Push subscription sends messages to the subscriber’s `/push` endpoint.  
   - The subscriber decodes the payload and inserts one row into the BigQuery `user_activity` table.

## GCP Setup

### 1. BigQuery

- Create a dataset (e.g. `activity`) in your project.
- Run the table DDL in `bigquery_schema.sql` (replace `PROJECT_ID` and `DATASET_ID`):

```bash
bq mk --dataset --location=us-central1 PROJECT_ID:DATASET_ID
# Then run the CREATE TABLE from bigquery_schema.sql in BigQuery console or:
bq query --use_legacy_sql=false < activity/bigquery_schema.sql
```

### 2. Pub/Sub

- Create a topic, e.g. `user-activity`:

```bash
gcloud pubsub topics create user-activity --project=YOUR_PROJECT_ID
```

- Backend env: set `PUBSUB_ACTIVITY_TOPIC=user-activity` (or full path `projects/PROJECT_ID/topics/user-activity`).

### 3. Subscriber (Cloud Run)

- Build and deploy the subscriber (from repo root):

```bash
cd activity_subscriber
gcloud run deploy activity-subscriber \
  --source . \
  --region=us-central1 \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID,BIGQUERY_DATASET_ID=activity,BIGQUERY_TABLE_ID=user_activity"
```

- Create a **push** subscription that sends to the Cloud Run URL:

```bash
gcloud pubsub subscriptions create activity-sub-push \
  --topic=user-activity \
  --push-endpoint=https://activity-subscriber-XXXXX.run.app/push \
  --project=YOUR_PROJECT_ID
```

(Use the actual URL of your Cloud Run service.)

- If the Cloud Run service is not public, use an authenticated push (IAM or OIDC) and configure the subscription accordingly.

## Backend env vars

| Variable | Description |
|---------|-------------|
| `GOOGLE_CLOUD_PROJECT` or `GCP_PROJECT_ID` | GCP project (for Pub/Sub and credentials). |
| `PUBSUB_ACTIVITY_TOPIC` | Topic name (e.g. `user-activity`) or full `projects/.../topics/...`. If unset, no events are published. |
| `GOOGLE_SERVICE_ACCOUNT_KEY` or `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON` | Service account JSON (path or inline). Must have **Pub/Sub Publisher** (e.g. `roles/pubsub.publisher`) for the topic. |

## Subscriber env vars (Cloud Run)

| Variable | Description |
|---------|-------------|
| `GOOGLE_CLOUD_PROJECT` or `GCP_PROJECT_ID` | GCP project. |
| `BIGQUERY_DATASET_ID` | BigQuery dataset (default `activity`). |
| `BIGQUERY_TABLE_ID` | BigQuery table (default `user_activity`). |

Cloud Run uses the default service account by default; give it **BigQuery Data Editor** (and **Job User** if you use load jobs) on the dataset/table.

## Adding more events

From any route that has `current_user`:

```python
from activity.publisher import publish_activity

publish_activity(
    "your_action_name",
    user_id=current_user.userid,
    user_phone=current_user.phone,
    resource_type="message",
    resource_id=str(some_id),
    metadata={"key": "value"},
)
```

## Querying activity in BigQuery

- Last 7 days for a user (by phone): filter `created_at` and `user_phone`.
- Counts by action: group by `action` and `DATE(created_at)`.
- Use `created_at` (partition column) in filters to keep scans small and cheap.
