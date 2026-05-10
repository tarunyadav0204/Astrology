-- Postgres: users.userid must auto-generate like SQLite INTEGER PRIMARY KEY.
-- Without a DEFAULT, INSERTs that omit userid fail with NOT NULL violation.
-- Run once per database (local + prod).

CREATE SEQUENCE IF NOT EXISTS users_userid_seq;

SELECT setval(
    'users_userid_seq',
    COALESCE((SELECT MAX(userid) FROM users), 0)
);

ALTER TABLE users
    ALTER COLUMN userid SET DEFAULT nextval('users_userid_seq'::regclass);

ALTER SEQUENCE users_userid_seq OWNED BY users.userid;
