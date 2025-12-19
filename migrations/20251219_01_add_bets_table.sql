-- Add bets table for wager tracking
-- depends: 20251217_01_initial_user_table

CREATE TABLE bet (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  participant1_id TEXT NOT NULL,
  participant2_id TEXT NOT NULL,
  description TEXT NOT NULL,
  details TEXT NULL,
  state TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by_discord_id TEXT NOT NULL,
  resolved_at TIMESTAMP NULL,
  resolved_by_discord_id TEXT NULL,
  winner_id TEXT NULL,
  resolution_notes TEXT NULL,
  FOREIGN KEY (participant1_id) REFERENCES user(id),
  FOREIGN KEY (participant2_id) REFERENCES user(id),
  FOREIGN KEY (winner_id) REFERENCES user(id),
  CHECK (participant1_id != participant2_id),
  CHECK (state IN ('active', 'resolved', 'cancelled')),
  CHECK (LENGTH(description) <= 280),
  CHECK (resolution_notes IS NULL OR LENGTH(resolution_notes) <= 280)
);

CREATE INDEX idx_bet_state ON bet(state);
CREATE INDEX idx_bet_created_at ON bet(created_at);
CREATE INDEX idx_bet_participant1 ON bet(participant1_id);
CREATE INDEX idx_bet_participant2 ON bet(participant2_id);
