-- Initial user table
-- depends:

CREATE TABLE user (
  id TEXT PRIMARY KEY,
  discord_id TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_discord_id ON user(discord_id);
