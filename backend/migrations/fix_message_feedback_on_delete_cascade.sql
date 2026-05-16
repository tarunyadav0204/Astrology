-- Ensure message_feedback rows are removed when chat_messages are deleted.
-- Run once on Postgres if account hard-delete fails with:
--   message_feedback_message_id_fkey ... Key (message_id)=(...) is still referenced
--
-- Safe to re-run: drops and recreates the same constraint name.

ALTER TABLE message_feedback
  DROP CONSTRAINT IF EXISTS message_feedback_message_id_fkey;

ALTER TABLE message_feedback
  ADD CONSTRAINT message_feedback_message_id_fkey
  FOREIGN KEY (message_id) REFERENCES chat_messages (message_id) ON DELETE CASCADE;
