import sqlite3
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_resolve_success_with_mention(mock_db, mock_ctx_with_guild, mock_interaction):
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

  mentioned_user = MagicMock()
  mentioned_user.id = 67890
  mentioned_user.display_name = 'Player2'
  mock_ctx_with_guild.message.mentions = [mentioned_user]

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import resolve

    await resolve(mock_ctx_with_guild, 101, 'Player2')

    mock_ctx_with_guild.channel.send.assert_called_once()
    call_args = mock_ctx_with_guild.channel.send.call_args
    assert 'r ya sure Player2 wins?' in call_args[0][0]
    assert 'view' in call_args[1]

    view = call_args[1]['view']
    await view.confirm.callback(mock_interaction)

    bet = cur.execute('SELECT * FROM bet WHERE id = 1').fetchone()
    assert bet[5] == 'resolved'
    assert bet[9] == '12345'
    assert bet[10] == p2_id

    mock_interaction.response.edit_message.assert_called_once()
    edit_call = mock_interaction.response.edit_message.call_args[1]['content']
    assert 'congrertulatiorns Player2' in edit_call
    assert 'betrr luck next time Player1' in edit_call


@pytest.mark.asyncio
async def test_resolve_success_with_display_name(mock_db, mock_ctx_with_guild, mock_interaction):
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

  mock_ctx_with_guild.message.mentions = []

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import resolve

    await resolve(mock_ctx_with_guild, 101, 'Player2')

    mock_ctx_with_guild.channel.send.assert_called_once()
    call_args = mock_ctx_with_guild.channel.send.call_args
    assert 'r ya sure Player2 wins?' in call_args[0][0]

    view = call_args[1]['view']
    await view.confirm.callback(mock_interaction)

    bet = cur.execute('SELECT * FROM bet WHERE id = 1').fetchone()
    assert bet[5] == 'resolved'
    assert bet[10] == p2_id


@pytest.mark.asyncio
async def test_resolve_participant1_wins(mock_db, mock_ctx_with_guild, mock_interaction):
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

  mock_ctx_with_guild.message.mentions = []

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import resolve

    await resolve(mock_ctx_with_guild, 101, 'Player1')

    view = mock_ctx_with_guild.channel.send.call_args[1]['view']
    await view.confirm.callback(mock_interaction)

    bet = cur.execute('SELECT * FROM bet WHERE id = 1').fetchone()
    assert bet[10] == p1_id


@pytest.mark.asyncio
async def test_resolve_either_participant_can_resolve(mock_db, mock_ctx_with_guild, mock_interaction):
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
    from casino.bot import resolve

    await resolve(mock_ctx_participant2, 101, 'Player1')

    mock_ctx_participant2.channel.send.assert_called_once()
    assert 'r ya sure Player1 wins?' in mock_ctx_participant2.channel.send.call_args[0][0]


@pytest.mark.asyncio
async def test_resolve_confirmation_button_nevrmind(mock_db, mock_ctx_with_guild, mock_interaction):
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

  mock_ctx_with_guild.message.mentions = []

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import resolve

    await resolve(mock_ctx_with_guild, 101, 'Player2')

    view = mock_ctx_with_guild.channel.send.call_args[1]['view']
    await view.cancel.callback(mock_interaction)

    bet = cur.execute('SELECT * FROM bet WHERE id = 1').fetchone()
    assert bet[5] == 'active'

    mock_interaction.response.edit_message.assert_called_once()


@pytest.mark.asyncio
async def test_resolve_with_notes(mock_db, mock_ctx_with_guild, mock_interaction):
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

  mock_ctx_with_guild.message.mentions = []

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import resolve

    await resolve(mock_ctx_with_guild, 101, 'Player2', notes='notes: player2 actually did it')

    view = mock_ctx_with_guild.channel.send.call_args[1]['view']
    await view.confirm.callback(mock_interaction)

    bet = cur.execute('SELECT * FROM bet WHERE id = 1').fetchone()
    assert bet[5] == 'resolved'
    assert bet[11] == 'player2 actually did it'


@pytest.mark.asyncio
async def test_resolve_bet_not_found(mock_db, mock_ctx_with_guild):
  con, cur = mock_db

  p1_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p1_id, 12345, 'Player1'))
  con.commit()

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import resolve

    await resolve(mock_ctx_with_guild, 1999, 'Player2')

    mock_ctx_with_guild.channel.send.assert_called_once_with(
      "i ain't know nothin bout that ticket numbr"
    )


@pytest.mark.asyncio
async def test_resolve_bet_already_resolved(mock_db, mock_ctx_with_guild):
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
    from casino.bot import resolve

    await resolve(mock_ctx_with_guild, 101, 'Player2')

    mock_ctx_with_guild.channel.send.assert_called_once_with(
      "cmon champ, that wager's long gone by now"
    )


@pytest.mark.asyncio
async def test_resolve_bet_already_cancelled(mock_db, mock_ctx_with_guild):
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
    from casino.bot import resolve

    await resolve(mock_ctx_with_guild, 101, 'Player2')

    mock_ctx_with_guild.channel.send.assert_called_once_with(
      "cmon champ, that wager's long gone by now"
    )


@pytest.mark.asyncio
async def test_resolve_not_a_participant(mock_db, mock_ctx_with_guild):
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
    from casino.bot import resolve

    await resolve(mock_ctx_with_guild, 101, 'Player2')

    mock_ctx_with_guild.channel.send.assert_called_once_with(
      "slow down pardner, you ain't a part of that there wager"
    )


@pytest.mark.asyncio
async def test_resolve_winner_not_participant(mock_db, mock_ctx_with_guild):
  con, cur = mock_db

  p1_id = str(uuid.uuid4())
  p2_id = str(uuid.uuid4())
  p3_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p1_id, 12345, 'Player1'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p2_id, 67890, 'Player2'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p3_id, 11111, 'Player3'))
  cur.execute('''INSERT INTO bet
                 (participant1_id, participant2_id, description, state, created_by_discord_id)
                 VALUES (?, ?, ?, 'active', ?)''',
              (p1_id, p2_id, 'Test bet', '12345'))
  con.commit()

  mock_ctx_with_guild.message.mentions = []

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import resolve

    await resolve(mock_ctx_with_guild, 101, 'Player3')

    mock_ctx_with_guild.channel.send.assert_called_once_with(
      "they aint a pard of this, its between Player1 and Player2"
    )


@pytest.mark.asyncio
async def test_resolve_notes_too_long(mock_db, mock_ctx_with_guild):
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

  long_notes = 'notes: ' + 'x' * 281

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import resolve

    await resolve(mock_ctx_with_guild, 101, 'Player2', notes=long_notes)

    mock_ctx_with_guild.channel.send.assert_called_once_with(
      'keep them notes under 280 characters pardner'
    )


@pytest.mark.asyncio
async def test_resolve_case_insensitive_display_name(mock_db, mock_ctx_with_guild, mock_interaction):
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

  mock_ctx_with_guild.message.mentions = []

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import resolve

    await resolve(mock_ctx_with_guild, 101, 'player2')

    mock_ctx_with_guild.channel.send.assert_called_once()
    assert 'r ya sure' in mock_ctx_with_guild.channel.send.call_args[0][0]


@pytest.mark.asyncio
async def test_resolve_database_fields_populated(mock_db, mock_ctx_with_guild, mock_interaction):
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

  mock_ctx_with_guild.message.mentions = []

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import resolve

    await resolve(mock_ctx_with_guild, 101, 'Player2', notes='notes: test notes')

    view = mock_ctx_with_guild.channel.send.call_args[1]['view']
    await view.confirm.callback(mock_interaction)

    bet = cur.execute('SELECT * FROM bet WHERE id = 1').fetchone()
    assert bet[5] == 'resolved'
    assert bet[8] is not None
    assert bet[9] == '12345'
    assert bet[10] == p2_id
    assert bet[11] == 'test notes'
