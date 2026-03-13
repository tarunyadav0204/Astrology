-- Add user_name column to existing user_activity table (run once if table was created before name was added).
-- Replace PROJECT_ID and DATASET_ID with your values (e.g. tradebest-465307 and activity).

ALTER TABLE `PROJECT_ID.DATASET_ID.user_activity`
ADD COLUMN IF NOT EXISTS user_name STRING OPTIONS(description = "User display name from JWT or current_user");
