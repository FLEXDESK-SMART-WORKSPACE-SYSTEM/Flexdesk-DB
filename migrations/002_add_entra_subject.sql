ALTER TABLE users ADD COLUMN IF NOT EXISTS entra_subject VARCHAR(255);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_entra_subject ON users (entra_subject);