-- Add bungo_dollars column to user table (before bungo_bux and spins)
-- depends: 20251221_01_add_spins

-- Create new table with bungo_dollars in the correct position
CREATE TABLE user_new (
  id TEXT PRIMARY KEY,
  discord_id TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  bungo_dollars INTEGER DEFAULT 0,
  bungo_bux INTEGER DEFAULT 0,
  spins INTEGER DEFAULT 0
);

-- Copy data from old table
INSERT INTO user_new (id, discord_id, display_name, created_at, bungo_bux, spins)
SELECT id, discord_id, display_name, created_at, bungo_bux, spins FROM user;

-- Calculate and populate bungo_dollars from existing bet history
UPDATE user_new
SET bungo_dollars = (
  SELECT COALESCE(SUM(
    CASE
      WHEN b.winner_id = user_new.id THEN 1
      WHEN (b.participant1_id = user_new.id OR b.participant2_id = user_new.id)
           AND b.winner_id IS NOT NULL
           AND b.winner_id != user_new.id THEN -1
      ELSE 0
    END
  ), 0)
  FROM bet b
  WHERE (b.participant1_id = user_new.id OR b.participant2_id = user_new.id)
    AND b.state = 'resolved'
);

-- Drop old table
DROP TABLE user;

-- Rename new table
ALTER TABLE user_new RENAME TO user;

-- Recreate index
CREATE INDEX idx_user_discord_id ON user(discord_id);
