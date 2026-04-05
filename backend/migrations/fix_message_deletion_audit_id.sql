-- Fix message_deletion_audit so INSERTs without audit_id work (audit_id auto-increments).
-- Run once on Postgres if deletes fail after audit insert errors (InFailedSqlTransaction).
-- Safe to run if sequence already exists: adjust or skip manually.

CREATE SEQUENCE IF NOT EXISTS message_deletion_audit_audit_id_seq;
SELECT setval(
    'message_deletion_audit_audit_id_seq',
    GREATEST(COALESCE((SELECT MAX(audit_id) FROM message_deletion_audit), 0), 1)
);
ALTER TABLE message_deletion_audit
  ALTER COLUMN audit_id SET DEFAULT nextval('message_deletion_audit_audit_id_seq');
ALTER SEQUENCE message_deletion_audit_audit_id_seq OWNED BY message_deletion_audit.audit_id;
