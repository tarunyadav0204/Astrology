# Activity logging setup – step by step

Do these in order. Start with **Step 1 (BigQuery)**.

---

## Step 1: BigQuery – create dataset and table

### 1.1 Open BigQuery

1. Go to [Google Cloud Console](https://console.cloud.google.com).
2. Select your project (or create one).
3. Open **BigQuery** (search “BigQuery” in the top bar or use the menu **☰ → BigQuery**).

### 1.2 Create the dataset

1. In the left panel, click your **project name**.
2. Click **⋮ (three dots)** next to the project → **Create dataset**.
3. Set:
   - **Dataset ID**: `activity`
   - **Data location**: `us-central1` (or your preferred region).
4. Click **Create dataset**.

### 1.3 Create the table

1. In the left panel, select the **activity** dataset.
2. Click **⋮** next to **activity** → **Create table**.
3. **Source**: “Empty table”.
4. **Table name**: `user_activity`.
5. Under **Schema**, switch to **Edit as text** and paste this (replace `YOUR_PROJECT_ID` with your GCP project ID):

```
event_id:STRING,
user_id:INTEGER,
user_phone:STRING,
action:STRING,
path:STRING,
method:STRING,
status_code:INTEGER,
duration_ms:FLOAT,
resource_type:STRING,
resource_id:STRING,
metadata:STRING,
ip:STRING,
user_agent:STRING,
created_at:TIMESTAMP
```

6. **Partitioning**:  
   - Enable “Partition by field”.  
   - Partition field: `created_at`.  
   - Partition type: **Day**.
7. **Clustering**:  
   - Add clustering fields: `action`, then `user_id`.
8. Click **Create table**.

**Alternative (bq CLI):** If you use `bq` and have replaced placeholders in the repo’s `bigquery_schema.sql`:

```bash
bq mk --dataset --location=us-central1 YOUR_PROJECT_ID:activity
bq query --use_legacy_sql=false --project_id=YOUR_PROJECT_ID < backend/activity/bigquery_schema.sql
```

After this, you should see dataset `activity` and table `user_activity` in BigQuery.  
Next: **Step 2 – Pub/Sub**.

---

## Step 2: Pub/Sub – create topic

### 2.1 Create the topic

1. In Google Cloud Console, go to **Pub/Sub → Topics** (or search “Pub/Sub”).
2. Click **Create topic**.
3. **Topic ID**: `user-activity`.
4. Leave other options as default.
5. Click **Create**.

**CLI:**

```bash
gcloud pubsub topics create user-activity --project=YOUR_PROJECT_ID
```

Replace `YOUR_PROJECT_ID` with your GCP project ID.

After this, the topic `user-activity` exists.  
Next: **Step 3 – Cloud Run subscriber**.

---

## Step 3: Cloud Run – deploy the subscriber

### 3.1 Deploy the service

From your **repo root** (where `activity_subscriber` folder is):

```bash
cd activity_subscriber
gcloud run deploy activity-subscriber \
  --source . \
  --region=us-central1 \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID,BIGQUERY_DATASET_ID=activity,BIGQUERY_TABLE_ID=user_activity"
```

Replace `YOUR_PROJECT_ID` with your real project ID.  
If `gcloud` asks to enable APIs, confirm.

### 3.2 Copy the service URL

When deploy finishes, the CLI prints the **Service URL**, e.g.:

`https://activity-subscriber-xxxxx-uc.a.run.app`

Copy this URL; you need it in Step 4. You can also find it in **Cloud Run → activity-subscriber → URL**.

Next: **Step 4 – Pub/Sub push subscription**.

---

## Step 4: Pub/Sub – create push subscription

### 4.1 Create the subscription

1. Go to **Pub/Sub → Subscriptions**.
2. Click **Create subscription**.
3. **Subscription ID**: `activity-sub-push`.
4. **Topic**: select `user-activity`.
5. **Delivery type**: **Push**.
6. **Endpoint URL**:  
   `https://YOUR-CLOUD-RUN-URL/push`  
   Example: `https://activity-subscriber-xxxxx-uc.a.run.app/push`
7. Leave other settings as default.
8. Click **Create**.

**CLI (replace the URL with your Cloud Run URL):**

```bash
gcloud pubsub subscriptions create activity-sub-push \
  --topic=user-activity \
  --push-endpoint=https://YOUR-CLOUD-RUN-URL/push \
  --project=YOUR_PROJECT_ID
```

### 4.2 Grant Pub/Sub permission to call Cloud Run

1. Go to **Cloud Run → activity-subscriber**.
2. Open the **Permissions** tab.
3. Click **Grant access**.
4. **Principal**: `service-XXXXX@gcp-sa-pubsub.iam.gserviceaccount.com`  
   (Find it under **Pub/Sub → Subscriptions → activity-sub-push → …**, or use the default compute SA.)
5. Or simpler: ensure the subscription uses the **default Pub/Sub service account** and that the Cloud Run service **allows unauthenticated** (you used `--allow-unauthenticated` in Step 3). Then no extra IAM is needed for push.

If push fails with 403, add the **Pub/Sub service account** as **Cloud Run Invoker** on the `activity-subscriber` service.

After this, messages published to `user-activity` are pushed to your subscriber.  
Next: **Step 5 – Backend env and IAM**.

---

## Step 5: Backend – env vars and IAM

### 5.1 Backend environment variables

On the machine (or container) where your FastAPI backend runs, set:

```env
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
PUBSUB_ACTIVITY_TOPIC=user-activity
```

Use the same **service account** as for Google Play / TTS (e.g. `GOOGLE_SERVICE_ACCOUNT_KEY` or `GOOGLE_APPLICATION_CREDENTIALS`).

### 5.2 Give that service account Pub/Sub publish permission

1. Go to **IAM & Admin → IAM**.
2. Find the service account your backend uses (the one in `GOOGLE_SERVICE_ACCOUNT_KEY`).
3. Click the pencil (Edit).
4. **Add another role**: **Pub/Sub Publisher** (`roles/pubsub.publisher`).
5. Save.

**CLI:**

```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT_EMAIL" \
  --role="roles/pubsub.publisher"
```

Replace `YOUR_SERVICE_ACCOUNT_EMAIL` with the `client_email` from your service account JSON.

### 5.3 Give Cloud Run’s service account BigQuery access

The subscriber runs as the **default Cloud Run service account** (or the one you set). It must be able to insert into BigQuery:

1. Go to **IAM & Admin → IAM**.
2. Find the Cloud Run service account (e.g. `YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com`, or the one shown in Cloud Run → activity-subscriber → **Security**).
3. Edit and add role: **BigQuery Data Editor** (`roles/bigquery.dataEditor`) – at project or dataset level.
4. Optionally add **BigQuery Job User** (`roles/bigquery.jobUser`) at project level if you use jobs.

**CLI (dataset-level; replace PROJECT_ID and dataset `activity` if different):**

```bash
# Get project number (optional, for default compute SA)
# Then grant BigQuery Data Editor on the dataset
bq add-iam-policy-binding \
  --member='serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com' \
  --role='roles/bigquery.dataEditor' \
  YOUR_PROJECT_ID:activity
```

After this, the backend can publish to `user-activity`, and the subscriber can write to `activity.user_activity`.  
Next: **Step 6 – Verify**.

---

## Step 6: Verify end-to-end

1. **Restart your FastAPI backend** (so it loads `PUBSUB_ACTIVITY_TOPIC` and the activity middleware).
2. Use the app (or call an API that triggers the middleware and/or a business event like podcast or purchase).
3. In **BigQuery**, run:

```sql
SELECT * FROM `YOUR_PROJECT_ID.activity.user_activity`
ORDER BY created_at DESC
LIMIT 20;
```

Replace `YOUR_PROJECT_ID` with your project ID. You should see new rows (e.g. `api_request`, `podcast_generated`, `credits_purchased`).

If no rows appear, check:

- Backend logs: “Activity: …” messages or Pub/Sub errors.
- Pub/Sub → **Subscriptions → activity-sub-push**: **Metrics** (message count, push errors).
- Cloud Run → **activity-subscriber**: **Logs** for errors on `/push`.

---

## Quick reference

| Step | What you created |
|------|-------------------|
| 1 | BigQuery dataset `activity`, table `user_activity` |
| 2 | Pub/Sub topic `user-activity` |
| 3 | Cloud Run service `activity-subscriber` (URL for `/push`) |
| 4 | Pub/Sub push subscription `activity-sub-push` → Cloud Run URL |
| 5 | Backend env: `GOOGLE_CLOUD_PROJECT`, `PUBSUB_ACTIVITY_TOPIC`; IAM: backend = Pub/Sub Publisher, subscriber = BigQuery Data Editor |
| 6 | Test and query BigQuery |
