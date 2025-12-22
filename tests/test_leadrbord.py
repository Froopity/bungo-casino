import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_leadrbord_no_resolved_bets(mock_db, mock_ctx):
  con, cur = mock_db

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import leadrbord

    await leadrbord(mock_ctx)

    mock_ctx.channel.send.assert_called_once_with("ain't nobody played yet pardner")


@pytest.mark.asyncio
async def test_leadrbord_displays_top_users(mock_db, mock_ctx):
  con, cur = mock_db

  user1_id = str(uuid.uuid4())
  user2_id = str(uuid.uuid4())
  user3_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)', (user1_id, 1001, 'Alice'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)', (user2_id, 1002, 'Bob'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)', (user3_id, 1003, 'Charlie'))

  cur.execute(
    'INSERT INTO bet (participant1_id, participant2_id, description, state, winner_id, created_by_discord_id) VALUES (?, ?, ?, ?, ?, ?)',
    (user1_id, user2_id, 'test1', 'resolved', user1_id, '1001')
  )
  cur.execute(
    'INSERT INTO bet (participant1_id, participant2_id, description, state, winner_id, created_by_discord_id) VALUES (?, ?, ?, ?, ?, ?)',
    (user1_id, user3_id, 'test2', 'resolved', user1_id, '1001')
  )
  cur.execute(
    'INSERT INTO bet (participant1_id, participant2_id, description, state, winner_id, created_by_discord_id) VALUES (?, ?, ?, ?, ?, ?)',
    (user2_id, user3_id, 'test3', 'resolved', user3_id, '1002')
  )
  con.commit()

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import leadrbord

    await leadrbord(mock_ctx)

    message = mock_ctx.channel.send.call_args[0][0]

    assert "big bungo's leadrbord" in message
    assert 'Alice' in message
    assert 'Bob' in message
    assert 'Charlie' in message
    assert '#1' in message
    assert '#2' in message
    assert '#3' in message


@pytest.mark.asyncio
async def test_leadrbord_balance_calculation(mock_db, mock_ctx):
  con, cur = mock_db

  user1_id = str(uuid.uuid4())
  user2_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)', (user1_id, 1001, 'Winner'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)', (user2_id, 1002, 'Loser'))

  cur.execute(
    'INSERT INTO bet (participant1_id, participant2_id, description, state, winner_id, created_by_discord_id) VALUES (?, ?, ?, ?, ?, ?)',
    (user1_id, user2_id, 'test1', 'resolved', user1_id, '1001')
  )
  cur.execute(
    'INSERT INTO bet (participant1_id, participant2_id, description, state, winner_id, created_by_discord_id) VALUES (?, ?, ?, ?, ?, ?)',
    (user1_id, user2_id, 'test2', 'resolved', user1_id, '1001')
  )
  cur.execute(
    'INSERT INTO bet (participant1_id, participant2_id, description, state, winner_id, created_by_discord_id) VALUES (?, ?, ?, ?, ?, ?)',
    (user1_id, user2_id, 'test3', 'resolved', user1_id, '1001')
  )

  cur.execute('UPDATE user SET bungo_dollars = 3 WHERE id = ?', (user1_id,))
  cur.execute('UPDATE user SET bungo_dollars = -3 WHERE id = ?', (user2_id,))

  con.commit()

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import leadrbord

    await leadrbord(mock_ctx)

    message = mock_ctx.channel.send.call_args[0][0]

    assert '$3' in message
    assert '-$3' in message
    assert '(3W/0L)' in message
    assert '(0W/3L)' in message


@pytest.mark.asyncio
async def test_leadrbord_excludes_cancelled_bets(mock_db, mock_ctx):
  con, cur = mock_db

  user1_id = str(uuid.uuid4())
  user2_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)', (user1_id, 1001, 'Alice'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)', (user2_id, 1002, 'Bob'))

  cur.execute(
    'INSERT INTO bet (participant1_id, participant2_id, description, state, winner_id, created_by_discord_id) VALUES (?, ?, ?, ?, ?, ?)',
    (user1_id, user2_id, 'test1', 'cancelled', user1_id, '1001')
  )
  cur.execute(
    'INSERT INTO bet (participant1_id, participant2_id, description, state, winner_id, created_by_discord_id) VALUES (?, ?, ?, ?, ?, ?)',
    (user1_id, user2_id, 'test2', 'active', None, '1001')
  )
  con.commit()

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import leadrbord

    await leadrbord(mock_ctx)

    mock_ctx.channel.send.assert_called_once_with("ain't nobody played yet pardner")


@pytest.mark.asyncio
async def test_leadrbord_tiebreaker_logic(mock_db, mock_ctx):
  con, cur = mock_db

  user1_id = str(uuid.uuid4())
  user2_id = str(uuid.uuid4())
  user3_id = str(uuid.uuid4())
  user4_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)', (user1_id, 1001, 'Alpha'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)', (user2_id, 1002, 'Beta'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)', (user3_id, 1003, 'Gamma'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)', (user4_id, 1004, 'Delta'))

  cur.execute(
    'INSERT INTO bet (participant1_id, participant2_id, description, state, winner_id, created_by_discord_id) VALUES (?, ?, ?, ?, ?, ?)',
    (user1_id, user3_id, 'test1', 'resolved', user1_id, '1001')
  )
  cur.execute(
    'INSERT INTO bet (participant1_id, participant2_id, description, state, winner_id, created_by_discord_id) VALUES (?, ?, ?, ?, ?, ?)',
    (user1_id, user4_id, 'test2', 'resolved', user4_id, '1001')
  )

  cur.execute(
    'INSERT INTO bet (participant1_id, participant2_id, description, state, winner_id, created_by_discord_id) VALUES (?, ?, ?, ?, ?, ?)',
    (user2_id, user3_id, 'test3', 'resolved', user2_id, '1002')
  )
  cur.execute(
    'INSERT INTO bet (participant1_id, participant2_id, description, state, winner_id, created_by_discord_id) VALUES (?, ?, ?, ?, ?, ?)',
    (user2_id, user4_id, 'test4', 'resolved', user2_id, '1002')
  )
  cur.execute(
    'INSERT INTO bet (participant1_id, participant2_id, description, state, winner_id, created_by_discord_id) VALUES (?, ?, ?, ?, ?, ?)',
    (user2_id, user3_id, 'test5', 'resolved', user3_id, '1002')
  )
  con.commit()

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import leadrbord

    await leadrbord(mock_ctx)

    message = mock_ctx.channel.send.call_args[0][0]
    lines = message.split('\n')

    user_lines = [line for line in lines if '#' in line]

    assert 'Beta' in user_lines[0]
    assert 'Alpha' in user_lines[1] or 'Delta' in user_lines[1]


@pytest.mark.asyncio
async def test_leadrbord_truncates_long_names(mock_db, mock_ctx):
  con, cur = mock_db

  user1_id = str(uuid.uuid4())
  user2_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)', (user1_id, 1001, 'VeryLongUserNameThatExceedsFifteenCharacters'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)', (user2_id, 1002, 'Bob'))

  cur.execute(
    'INSERT INTO bet (participant1_id, participant2_id, description, state, winner_id, created_by_discord_id) VALUES (?, ?, ?, ?, ?, ?)',
    (user1_id, user2_id, 'test1', 'resolved', user1_id, '1001')
  )
  con.commit()

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import leadrbord

    await leadrbord(mock_ctx)

    message = mock_ctx.channel.send.call_args[0][0]

    assert 'VeryLongUserNam...' in message
    assert 'VeryLongUserNameThatExceedsFifteenCharacters' not in message


@pytest.mark.asyncio
async def test_leadrbord_fewer_than_10_users(mock_db, mock_ctx):
  con, cur = mock_db

  user1_id = str(uuid.uuid4())
  user2_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)', (user1_id, 1001, 'Alice'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)', (user2_id, 1002, 'Bob'))

  cur.execute(
    'INSERT INTO bet (participant1_id, participant2_id, description, state, winner_id, created_by_discord_id) VALUES (?, ?, ?, ?, ?, ?)',
    (user1_id, user2_id, 'test1', 'resolved', user1_id, '1001')
  )
  con.commit()

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import leadrbord

    await leadrbord(mock_ctx)

    message = mock_ctx.channel.send.call_args[0][0]

    assert '#1' in message
    assert '#2' in message
    assert '#3' not in message


@pytest.mark.asyncio
async def test_leadrbord_limits_to_10_users(mock_db, mock_ctx):
  con, cur = mock_db

  user_ids = []
  for i in range(15):
    user_id = str(uuid.uuid4())
    user_ids.append(user_id)
    cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)', (user_id, 2000+i, f'User{i}'))

  for i in range(14):
    cur.execute(
      'INSERT INTO bet (participant1_id, participant2_id, description, state, winner_id, created_by_discord_id) VALUES (?, ?, ?, ?, ?, ?)',
      (user_ids[i], user_ids[i+1], f'test{i}', 'resolved', user_ids[i], str(2000+i))
    )
  con.commit()

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import leadrbord

    await leadrbord(mock_ctx)

    message = mock_ctx.channel.send.call_args[0][0]

    assert '#10' in message
    assert '#11' not in message


@pytest.mark.asyncio
async def test_leaderboard_alias_works(mock_db, mock_ctx):
  con, cur = mock_db

  user1_id = str(uuid.uuid4())
  user2_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)', (user1_id, 1001, 'Alice'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)', (user2_id, 1002, 'Bob'))

  cur.execute(
    'INSERT INTO bet (participant1_id, participant2_id, description, state, winner_id, created_by_discord_id) VALUES (?, ?, ?, ?, ?, ?)',
    (user1_id, user2_id, 'test1', 'resolved', user1_id, '1001')
  )
  con.commit()

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import leadrbord

    await leadrbord(mock_ctx)

    message = mock_ctx.channel.send.call_args[0][0]

    assert "big bungo's leadrbord" in message
    assert 'Alice' in message
