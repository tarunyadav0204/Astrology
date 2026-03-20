-- Create BigQuery dataset and table for user activity (run in BigQuery console or bq CLI).
-- Replace PROJECT_ID and DATASET_ID with your values.

-- 1. Create dataset (if not exists)
-- CREATE SCHEMA IF NOT EXISTS `PROJECT_ID.DATASET_ID`
--   OPTIONS(location = "us-central1");

-- 2. Create partitioned table for activity events
-- Partition by date(created_at) for cheap, fast date-range queries.

CREATE TABLE IF NOT EXISTS `PROJECT_ID.DATASET_ID.user_activity` (
  event_id STRING OPTIONS(description = "Unique event id (e.g. from Pub/Sub messageId)"),
  user_id INT64 OPTIONS(description = "User id from app DB when available"),
  user_phone STRING OPTIONS(description = "Phone from JWT sub when user_id not set"),
  user_name STRING OPTIONS(description = "User display name from JWT or current_user"),
  action STRING NOT NULL OPTIONS(description = "e.g. api_request, podcast_generated, credits_purchased"),
  path STRING OPTIONS(description = "API path for api_request"),
  method STRING OPTIONS(description = "HTTP method"),
  status_code INT64 OPTIONS(description = "HTTP status code"),
  duration_ms FLOAT64 OPTIONS(description = "Request duration in ms"),
  resource_type STRING OPTIONS(description = "e.g. message, chart"),
  resource_id STRING OPTIONS(description = "Related entity id"),
  metadata STRING OPTIONS(description = "JSON string for extra data"),
  error_type STRING OPTIONS(description = "Exception type (for api_error)"),
  error_message STRING OPTIONS(description = "Error message (for api_error)"),
  stack_trace STRING OPTIONS(description = "Full stack trace (for api_error)"),
  ip STRING OPTIONS(description = "Client IP"),
  user_agent STRING OPTIONS(description = "Client user agent"),
  created_at TIMESTAMP NOT NULL OPTIONS(description = "Event time UTC")
)
PARTITION BY DATE(created_at)
CLUSTER BY action, user_id
OPTIONS(
  description = "User activity events from app (Pub/Sub -> subscriber)",
  require_partition_filter = false
);

-- Example queries:
-- Last 7 days for a user (by phone):
-- SELECT * FROM `PROJECT_ID.DATASET_ID.user_activity`
-- WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY) AND user_phone = '+1234567890'
-- ORDER BY created_at DESC LIMIT 100;

-- Count by action last 30 days:
-- SELECT action, COUNT(*) as cnt FROM `PROJECT_ID.DATASET_ID.user_activity`
-- WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
-- GROUP BY action ORDER BY cnt DESC;
