-- Add role column to users table if it doesn't exist
ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user';

-- Make user 9810690066 an admin
UPDATE users SET role = 'admin' WHERE phone = '9810690066';

-- Verify admin user
SELECT phone, name, role FROM users WHERE role = 'admin';