-- Demo data for casino database

-- Insert demo users
INSERT INTO user (id, discord_id, display_name, bungo_dollars, bungo_bux, spins) VALUES
  ('user_alice', '123456789012345678', 'Alice', 0, 100, 5),
  ('user_bob', '234567890123456789', 'Bob', 0, 50, 3),
  ('user_charlie', '345678901234567890', 'Charlie', 0, 25, 1),
  ('user_dave', '456789012345678901', 'Dave', 0, 75, 4),
  ('user_eve', '567890123456789012', 'Eve', 0, 30, 2),
  ('user_frank', '678901234567890123', 'Frank', 0, 60, 3);

-- Insert resolved wagers
INSERT INTO bet (
  participant1_id,
  participant2_id,
  description,
  state,
  created_by_discord_id,
  resolved_at,
  resolved_by_discord_id,
  winner_id
) VALUES
  ('user_alice', 'user_bob', 'Alice bets Bob can''t eat 50 chicken nuggets', 'resolved', '123456789012345678', datetime('now', '-30 days'), '234567890123456789', 'user_alice'),
  ('user_bob', 'user_charlie', 'Bob bets Charlie will be late', 'resolved', '234567890123456789', datetime('now', '-29 days'), '123456789012345678', 'user_charlie'),
  ('user_alice', 'user_charlie', 'Alice bets Discord will break', 'resolved', '123456789012345678', datetime('now', '-28 days'), '234567890123456789', 'user_alice'),
  ('user_dave', 'user_alice', 'Dave bets the weather will be sunny', 'resolved', '456789012345678901', datetime('now', '-27 days'), '123456789012345678', 'user_alice'),
  ('user_eve', 'user_frank', 'Eve bets Frank can''t solve the puzzle', 'resolved', '567890123456789012', datetime('now', '-26 days'), '678901234567890123', 'user_frank'),
  ('user_alice', 'user_dave', 'Alice bets coffee runs out by noon', 'resolved', '123456789012345678', datetime('now', '-25 days'), '456789012345678901', 'user_alice'),
  ('user_bob', 'user_eve', 'Bob bets the build will fail', 'resolved', '234567890123456789', datetime('now', '-24 days'), '567890123456789012', 'user_bob'),
  ('user_charlie', 'user_frank', 'Charlie bets it''ll rain tomorrow', 'resolved', '345678901234567890', datetime('now', '-23 days'), '678901234567890123', 'user_frank'),
  ('user_dave', 'user_bob', 'Dave bets the meeting goes over time', 'resolved', '456789012345678901', datetime('now', '-22 days'), '234567890123456789', 'user_dave'),
  ('user_eve', 'user_alice', 'Eve bets the printer jams', 'resolved', '567890123456789012', datetime('now', '-21 days'), '123456789012345678', 'user_alice'),
  ('user_frank', 'user_charlie', 'Frank bets lunch arrives late', 'resolved', '678901234567890123', datetime('now', '-20 days'), '345678901234567890', 'user_frank'),
  ('user_alice', 'user_bob', 'Alice bets Bob oversleeps', 'resolved', '123456789012345678', datetime('now', '-19 days'), '234567890123456789', 'user_alice'),
  ('user_bob', 'user_dave', 'Bob bets Dave forgets his laptop', 'resolved', '234567890123456789', datetime('now', '-18 days'), '456789012345678901', 'user_bob'),
  ('user_charlie', 'user_eve', 'Charlie bets Eve wins the game', 'resolved', '345678901234567890', datetime('now', '-17 days'), '567890123456789012', 'user_eve'),
  ('user_dave', 'user_frank', 'Dave bets Frank picks wrong answer', 'resolved', '456789012345678901', datetime('now', '-16 days'), '678901234567890123', 'user_dave'),
  ('user_eve', 'user_charlie', 'Eve bets Charlie gets lost', 'resolved', '567890123456789012', datetime('now', '-15 days'), '345678901234567890', 'user_charlie'),
  ('user_frank', 'user_alice', 'Frank bets Alice misses deadline', 'resolved', '678901234567890123', datetime('now', '-14 days'), '123456789012345678', 'user_alice'),
  ('user_alice', 'user_charlie', 'Alice bets it snows tonight', 'resolved', '123456789012345678', datetime('now', '-13 days'), '345678901234567890', 'user_alice'),
  ('user_bob', 'user_frank', 'Bob bets Frank can''t finish pizza', 'resolved', '234567890123456789', datetime('now', '-12 days'), '678901234567890123', 'user_bob'),
  ('user_charlie', 'user_dave', 'Charlie bets Dave will be early', 'resolved', '345678901234567890', datetime('now', '-11 days'), '456789012345678901', 'user_dave'),
  ('user_dave', 'user_eve', 'Dave bets Eve knows the answer', 'resolved', '456789012345678901', datetime('now', '-10 days'), '567890123456789012', 'user_eve'),
  ('user_eve', 'user_bob', 'Eve bets Bob breaks something', 'resolved', '567890123456789012', datetime('now', '-9 days'), '234567890123456789', 'user_bob'),
  ('user_frank', 'user_dave', 'Frank bets Dave loses his keys', 'resolved', '678901234567890123', datetime('now', '-8 days'), '456789012345678901', 'user_frank'),
  ('user_alice', 'user_eve', 'Alice bets Eve arrives first', 'resolved', '123456789012345678', datetime('now', '-7 days'), '567890123456789012', 'user_alice'),
  ('user_bob', 'user_charlie', 'Bob bets Charlie gets the joke', 'resolved', '234567890123456789', datetime('now', '-6 days'), '345678901234567890', 'user_bob'),
  ('user_charlie', 'user_alice', 'Charlie bets Alice wins debate', 'resolved', '345678901234567890', datetime('now', '-5 days'), '123456789012345678', 'user_alice'),
  ('user_dave', 'user_charlie', 'Dave bets Charlie picks heads', 'resolved', '456789012345678901', datetime('now', '-4 days'), '345678901234567890', 'user_charlie'),
  ('user_eve', 'user_dave', 'Eve bets Dave finds the bug', 'resolved', '567890123456789012', datetime('now', '-3 days'), '456789012345678901', 'user_dave'),
  ('user_frank', 'user_bob', 'Frank bets Bob remembers password', 'resolved', '678901234567890123', datetime('now', '-2 days'), '234567890123456789', 'user_bob'),
  ('user_alice', 'user_frank', 'Alice bets Frank makes typo', 'resolved', '123456789012345678', datetime('now', '-1 day'), '678901234567890123', 'user_alice'),
  ('user_bob', 'user_alice', 'Bob bets Alice drinks coffee', 'resolved', '234567890123456789', datetime('now', '-23 hours'), '123456789012345678', 'user_alice'),
  ('user_charlie', 'user_bob', 'Charlie bets Bob wears hoodie', 'resolved', '345678901234567890', datetime('now', '-22 hours'), '234567890123456789', 'user_bob'),
  ('user_dave', 'user_alice', 'Dave bets Alice codes in Python', 'resolved', '456789012345678901', datetime('now', '-21 hours'), '123456789012345678', 'user_alice'),
  ('user_eve', 'user_frank', 'Eve bets Frank uses dark mode', 'resolved', '567890123456789012', datetime('now', '-20 hours'), '678901234567890123', 'user_frank'),
  ('user_frank', 'user_eve', 'Frank bets Eve has headphones', 'resolved', '678901234567890123', datetime('now', '-19 hours'), '567890123456789012', 'user_eve'),
  ('user_alice', 'user_dave', 'Alice bets Dave uses vim', 'resolved', '123456789012345678', datetime('now', '-18 hours'), '456789012345678901', 'user_alice'),
  ('user_bob', 'user_dave', 'Bob bets Dave solves it first', 'resolved', '234567890123456789', datetime('now', '-17 hours'), '456789012345678901', 'user_dave'),
  ('user_charlie', 'user_alice', 'Charlie bets Alice pushes to main', 'resolved', '345678901234567890', datetime('now', '-16 hours'), '123456789012345678', 'user_alice'),
  ('user_dave', 'user_bob', 'Dave bets Bob reviews PR fast', 'resolved', '456789012345678901', datetime('now', '-15 hours'), '234567890123456789', 'user_dave'),
  ('user_eve', 'user_charlie', 'Eve bets Charlie merges today', 'resolved', '567890123456789012', datetime('now', '-14 hours'), '345678901234567890', 'user_charlie'),
  ('user_frank', 'user_alice', 'Frank bets Alice fixes the bug', 'resolved', '678901234567890123', datetime('now', '-13 hours'), '123456789012345678', 'user_alice'),
  ('user_alice', 'user_eve', 'Alice bets Eve deploys successfully', 'resolved', '123456789012345678', datetime('now', '-12 hours'), '567890123456789012', 'user_alice'),
  ('user_bob', 'user_frank', 'Bob bets Frank writes tests', 'resolved', '234567890123456789', datetime('now', '-11 hours'), '678901234567890123', 'user_bob'),
  ('user_charlie', 'user_dave', 'Charlie bets Dave refactors code', 'resolved', '345678901234567890', datetime('now', '-10 hours'), '456789012345678901', 'user_dave'),
  ('user_dave', 'user_frank', 'Dave bets Frank ships feature', 'resolved', '456789012345678901', datetime('now', '-9 hours'), '678901234567890123', 'user_frank'),
  ('user_eve', 'user_alice', 'Eve bets Alice finds edge case', 'resolved', '567890123456789012', datetime('now', '-8 hours'), '123456789012345678', 'user_alice'),
  ('user_frank', 'user_charlie', 'Frank bets Charlie optimizes query', 'resolved', '678901234567890123', datetime('now', '-7 hours'), '345678901234567890', 'user_frank'),
  ('user_alice', 'user_bob', 'Alice bets Bob breaks build', 'resolved', '123456789012345678', datetime('now', '-6 hours'), '234567890123456789', 'user_bob'),
  ('user_bob', 'user_charlie', 'Bob bets Charlie adds feature flag', 'resolved', '234567890123456789', datetime('now', '-5 hours'), '345678901234567890', 'user_charlie'),
  ('user_charlie', 'user_eve', 'Charlie bets Eve catches the typo', 'resolved', '345678901234567890', datetime('now', '-4 hours'), '567890123456789012', 'user_eve'),
  ('user_dave', 'user_alice', 'Dave bets Alice ships on time', 'resolved', '456789012345678901', datetime('now', '-3 hours'), '123456789012345678', 'user_alice'),
  ('user_eve', 'user_bob', 'Eve bets Bob documents the API', 'resolved', '567890123456789012', datetime('now', '-2 hours'), '234567890123456789', 'user_bob'),
  ('user_frank', 'user_dave', 'Frank bets Dave handles error case', 'resolved', '678901234567890123', datetime('now', '-1 hour'), '456789012345678901', 'user_frank');

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
