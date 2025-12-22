-- Demo data for casino database

-- Insert demo users
INSERT INTO user (id, discord_id, display_name, bungo_dollars, bungo_bux, spins) VALUES
  ('user_alice', '123456789012345678', 'Alice', 2, 100, 5),
  ('user_bob', '234567890123456789', 'Bob', -1, 50, 3),
  ('user_charlie', '345678901234567890', 'Charlie', -1, 25, 1);

-- Insert resolved wagers
INSERT INTO bet (
  participant1_id,
  participant2_id,
  description,
  details,
  state,
  created_by_discord_id,
  resolved_at,
  resolved_by_discord_id,
  winner_id,
  resolution_notes
) VALUES
  (
    'user_alice',
    'user_bob',
    'Alice bets Bob can''t eat 50 chicken nuggets in one sitting',
    'Bob claimed he could easily do it. Alice doubted.',
    'resolved',
    '123456789012345678',
    datetime('now', '-2 days'),
    '234567890123456789',
    'user_alice',
    'Bob gave up after 37 nuggets'
  ),
  (
    'user_bob',
    'user_charlie',
    'Bob bets Charlie will be late to the next meeting',
    NULL,
    'resolved',
    '234567890123456789',
    datetime('now', '-1 day'),
    '123456789012345678',
    'user_charlie',
    'Charlie arrived 5 minutes early'
  ),
  (
    'user_alice',
    'user_charlie',
    'Alice bets the next Discord update will break something',
    'Charlie thinks Discord devs have their act together now',
    'resolved',
    '123456789012345678',
    datetime('now', '-3 hours'),
    '234567890123456789',
    'user_alice',
    'Voice channels stopped working for 2 hours'
  );

-- Insert unresolved wagers
INSERT INTO bet (
  participant1_id,
  participant2_id,
  description,
  details,
  state,
  created_by_discord_id
) VALUES
  (
    'user_alice',
    'user_bob',
    'Alice bets it will snow before New Year',
    'Bob says no way, too warm this year',
    'active',
    '123456789012345678'
  ),
  (
    'user_charlie',
    'user_alice',
    'Charlie bets the coffee machine breaks again within a week',
    'Alice has faith in the new repair',
    'active',
    '345678901234567890'
  );
