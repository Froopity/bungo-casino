import sqlite3
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_cancel_success(mock_db, mock_ctx_with_guild, mock_interaction):
  con, cur = mock_db

  p1_id = str(uuid.uuid4())
  p2_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p1_id, 12345, 'Player1'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p2_id, 67890, 'Player2'))
  cur.execute('''INSERT INTO bet
                 (participant1_id, participant2_id, description, state, created_by_discord_id)
                 VALUES (?, ?, ?, 'active', ?)''',
              (p1_id, p2_id, 'Test bet', '12345'))
  con.commit()

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import cancel

    await cancel(mock_ctx_with_guild, 1)

    mock_ctx_with_guild.channel.send.assert_called_once()
    call_args = mock_ctx_with_guild.channel.send.call_args
    assert 'r ya sure?' in call_args[0][0]
    assert 'view' in call_args[1]

    view = call_args[1]['view']
    await view.confirm.callback(mock_interaction)

    bet = cur.execute('SELECT * FROM bet WHERE id = 1').fetchone()
    assert bet[5] == 'cancelled'

    mock_interaction.response.edit_message.assert_called_once()
    edit_call = mock_interaction.response.edit_message.call_args[1]['content']
    assert 'ah well' in edit_call


@pytest.mark.asyncio
async def test_cancel_either_participant_can_cancel(mock_db, mock_ctx_with_guild, mock_interaction):
  con, cur = mock_db

  p1_id = str(uuid.uuid4())
  p2_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p1_id, 12345, 'Player1'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p2_id, 67890, 'Player2'))
  cur.execute('''INSERT INTO bet
                 (participant1_id, participant2_id, description, state, created_by_discord_id)
                 VALUES (?, ?, ?, 'active', ?)''',
              (p1_id, p2_id, 'Test bet', '12345'))
  con.commit()

  mock_ctx_participant2 = MagicMock()
  mock_ctx_participant2.author = MagicMock()
  mock_ctx_participant2.author.id = 67890
  mock_ctx_participant2.channel = MagicMock()
  mock_ctx_participant2.channel.send = AsyncMock()
  mock_ctx_participant2.message = MagicMock()
  mock_ctx_participant2.message.mentions = []
  mock_ctx_participant2.guild = mock_ctx_with_guild.guild

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import cancel

    await cancel(mock_ctx_participant2, 1)

    mock_ctx_participant2.channel.send.assert_called_once()
    assert 'r ya sure?' in mock_ctx_participant2.channel.send.call_args[0][0]


@pytest.mark.asyncio
async def test_cancel_confirmation_button_nevrmind(mock_db, mock_ctx_with_guild, mock_interaction):
  con, cur = mock_db

  p1_id = str(uuid.uuid4())
  p2_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p1_id, 12345, 'Player1'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p2_id, 67890, 'Player2'))
  cur.execute('''INSERT INTO bet
                 (participant1_id, participant2_id, description, state, created_by_discord_id)
                 VALUES (?, ?, ?, 'active', ?)''',
              (p1_id, p2_id, 'Test bet', '12345'))
  con.commit()

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import cancel

    await cancel(mock_ctx_with_guild, 1)

    view = mock_ctx_with_guild.channel.send.call_args[1]['view']
    await view.cancel.callback(mock_interaction)

    bet = cur.execute('SELECT * FROM bet WHERE id = 1').fetchone()
    assert bet[5] == 'active'

    mock_interaction.response.edit_message.assert_called_once()
    edit_call = mock_interaction.response.edit_message.call_args[1]['content']
    assert 'alright pardner, cancellation cancelled' in edit_call


@pytest.mark.asyncio
async def test_cancel_canceller_not_registered(mock_db, mock_ctx_with_guild):
  con, cur = mock_db

  p1_id = str(uuid.uuid4())
  p2_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p1_id, 99999, 'Player1'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p2_id, 67890, 'Player2'))
  cur.execute('''INSERT INTO bet
                 (participant1_id, participant2_id, description, state, created_by_discord_id)
                 VALUES (?, ?, ?, 'active', ?)''',
              (p1_id, p2_id, 'Test bet', '99999'))
  con.commit()

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import cancel

    await cancel(mock_ctx_with_guild, 1)

    mock_ctx_with_guild.channel.send.assert_called_once_with(
      'woaah slow down ther cowboy, you gotta say $howdy first'
    )


@pytest.mark.asyncio
async def test_cancel_bet_not_found(mock_db, mock_ctx_with_guild):
  con, cur = mock_db

  p1_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p1_id, 12345, 'Player1'))
  con.commit()

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import cancel

    await cancel(mock_ctx_with_guild, 999)

    mock_ctx_with_guild.channel.send.assert_called_once_with(
      "i ain't know nothin bout that ticket numbr"
    )


@pytest.mark.asyncio
async def test_cancel_bet_already_resolved(mock_db, mock_ctx_with_guild):
  con, cur = mock_db

  p1_id = str(uuid.uuid4())
  p2_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p1_id, 12345, 'Player1'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p2_id, 67890, 'Player2'))
  cur.execute('''INSERT INTO bet
                 (participant1_id, participant2_id, description, state, created_by_discord_id, winner_id)
                 VALUES (?, ?, ?, 'resolved', ?, ?)''',
              (p1_id, p2_id, 'Test bet', '12345', p1_id))
  con.commit()

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import cancel

    await cancel(mock_ctx_with_guild, 1)

    mock_ctx_with_guild.channel.send.assert_called_once_with(
      "cmon champ, that wager's long gone by now"
    )


@pytest.mark.asyncio
async def test_cancel_bet_already_cancelled(mock_db, mock_ctx_with_guild):
  con, cur = mock_db

  p1_id = str(uuid.uuid4())
  p2_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p1_id, 12345, 'Player1'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p2_id, 67890, 'Player2'))
  cur.execute('''INSERT INTO bet
                 (participant1_id, participant2_id, description, state, created_by_discord_id)
                 VALUES (?, ?, ?, 'cancelled', ?)''',
              (p1_id, p2_id, 'Test bet', '12345'))
  con.commit()

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import cancel

    await cancel(mock_ctx_with_guild, 1)

    mock_ctx_with_guild.channel.send.assert_called_once_with(
      "cmon champ, that wager's long gone by now"
    )


@pytest.mark.asyncio
async def test_cancel_not_a_participant(mock_db, mock_ctx_with_guild):
  con, cur = mock_db

  p1_id = str(uuid.uuid4())
  p2_id = str(uuid.uuid4())
  p3_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p1_id, 99999, 'Player1'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p2_id, 67890, 'Player2'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p3_id, 12345, 'Player3'))
  cur.execute('''INSERT INTO bet
                 (participant1_id, participant2_id, description, state, created_by_discord_id)
                 VALUES (?, ?, ?, 'active', ?)''',
              (p1_id, p2_id, 'Test bet', '99999'))
  con.commit()

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import cancel

    await cancel(mock_ctx_with_guild, 1)

    mock_ctx_with_guild.channel.send.assert_called_once_with(
      "slow down pardner, you ain't a part of that there wager"
    )


@pytest.mark.asyncio
async def test_cancel_race_condition(mock_db, mock_ctx_with_guild, mock_interaction):
  con, cur = mock_db

  p1_id = str(uuid.uuid4())
  p2_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p1_id, 12345, 'Player1'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p2_id, 67890, 'Player2'))
  cur.execute('''INSERT INTO bet
                 (participant1_id, participant2_id, description, state, created_by_discord_id)
                 VALUES (?, ?, ?, 'active', ?)''',
              (p1_id, p2_id, 'Test bet', '12345'))
  con.commit()

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import cancel

    await cancel(mock_ctx_with_guild, 1)

    view = mock_ctx_with_guild.channel.send.call_args[1]['view']

    cur.execute("UPDATE bet SET state = 'cancelled' WHERE id = 1")
    con.commit()

    await view.confirm.callback(mock_interaction)

    mock_interaction.response.edit_message.assert_called_once()
    edit_call = mock_interaction.response.edit_message.call_args[1]['content']
    assert "cmon champ, that wager's long gone by now" in edit_call


@pytest.mark.asyncio
async def test_cancel_database_state_updated(mock_db, mock_ctx_with_guild, mock_interaction):
  con, cur = mock_db

  p1_id = str(uuid.uuid4())
  p2_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p1_id, 12345, 'Player1'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p2_id, 67890, 'Player2'))
  cur.execute('''INSERT INTO bet
                 (participant1_id, participant2_id, description, state, created_by_discord_id)
                 VALUES (?, ?, ?, 'active', ?)''',
              (p1_id, p2_id, 'Test bet', '12345'))
  con.commit()

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import cancel

    await cancel(mock_ctx_with_guild, 1)

    view = mock_ctx_with_guild.channel.send.call_args[1]['view']
    await view.confirm.callback(mock_interaction)

    bet = cur.execute('SELECT state FROM bet WHERE id = 1').fetchone()
    assert bet[0] == 'cancelled'
