import uuid
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_wager_success_with_mention(mock_db, mock_ctx_with_guild, mock_bot):
  con, cur = mock_db

  creator_id = str(uuid.uuid4())
  opponent_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (creator_id, 12345, 'TestCreator'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (opponent_id, 67890, 'TestOpponent'))
  con.commit()

  mentioned_user = MagicMock()
  mentioned_user.id = 67890
  mentioned_user.display_name = 'TestOpponent'
  mock_ctx_with_guild.message.mentions = [mentioned_user]

  with patch('casino.bot.con', con), patch('casino.bot.bot', mock_bot):
    from casino.bot import wager

    await wager(mock_ctx_with_guild, '@TestOpponent', description='I can juggle 5 balls')

    mock_ctx_with_guild.channel.send.assert_called_once()
    call_args = mock_ctx_with_guild.channel.send.call_args[0][0]
    assert 'alrighty your ticket is' in call_args
    assert 'good luck champ' in call_args

    bet = cur.execute('SELECT * FROM bet WHERE id = 1').fetchone()
    assert bet is not None
    assert bet[1] == creator_id
    assert bet[2] == opponent_id
    assert bet[3] == 'I can juggle 5 balls'
    assert bet[5] == 'active'


@pytest.mark.asyncio
async def test_wager_success_with_display_name(mock_db, mock_ctx_with_guild, mock_bot):
  con, cur = mock_db

  creator_id = str(uuid.uuid4())
  opponent_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (creator_id, 12345, 'TestCreator'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (opponent_id, 67890, 'TestOpponent'))
  con.commit()

  mentioned_user = MagicMock()
  mentioned_user.id = 67890
  mentioned_user.display_name = 'TestOpponent'
  mock_ctx_with_guild.message.mentions = [mentioned_user]

  with patch('casino.bot.con', con), patch('casino.bot.bot', mock_bot):
    from casino.bot import wager

    await wager(mock_ctx_with_guild, 'TestOpponent', description='I can eat 10 hot dogs')

    mock_ctx_with_guild.channel.send.assert_called_once()
    call_args = mock_ctx_with_guild.channel.send.call_args[0][0]
    assert 'alrighty your ticket is' in call_args

    bet = cur.execute('SELECT * FROM bet WHERE id = 1').fetchone()
    assert bet is not None
    assert bet[3] == 'I can eat 10 hot dogs'


@pytest.mark.asyncio
async def test_wager_self_betting_with_mention(mock_db, mock_ctx_with_guild, mock_bot):
  con, cur = mock_db

  creator_id = str(uuid.uuid4())
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (creator_id, 12345, 'TestCreator'))
  con.commit()

  mentioned_user = MagicMock()
  mentioned_user.id = 12345
  mentioned_user.display_name = 'TestCreator'
  mock_ctx_with_guild.message.mentions = [mentioned_user]

  with patch('casino.bot.con', con), patch('casino.bot.bot', mock_bot):
    from casino.bot import wager

    await wager(mock_ctx_with_guild, '@TestCreator', description='test bet')

    mock_ctx_with_guild.channel.send.assert_called_once_with(
      'you cant place a wager on urself!'
    )


@pytest.mark.asyncio
async def test_wager_self_betting_with_display_name(mock_db, mock_ctx_with_guild, mock_bot):
  con, cur = mock_db

  creator_id = str(uuid.uuid4())
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (creator_id, 12345, 'TestCreator'))
  con.commit()

  mentioned_user = MagicMock()
  mentioned_user.id = 12345
  mentioned_user.display_name = 'TestCreator'
  mock_ctx_with_guild.message.mentions = [mentioned_user]

  with patch('casino.bot.con', con), patch('casino.bot.bot', mock_bot):
    from casino.bot import wager

    await wager(mock_ctx_with_guild, 'TestCreator', description='test bet')

    mock_ctx_with_guild.channel.send.assert_called_once_with(
      'you cant place a wager on urself!'
    )


@pytest.mark.asyncio
async def test_wager_opponent_not_registered_mention(mock_db, mock_ctx_with_guild, mock_bot):
  con, cur = mock_db

  creator_id = str(uuid.uuid4())
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (creator_id, 12345, 'TestCreator'))
  con.commit()

  mentioned_user = MagicMock()
  mentioned_user.id = 67890
  mentioned_user.display_name = 'TestOpponent'
  mock_ctx_with_guild.message.mentions = [mentioned_user]

  with patch('casino.bot.con', con), patch('casino.bot.bot', mock_bot):
    from casino.bot import wager

    await wager(mock_ctx_with_guild, '@TestOpponent', description='test bet')

    mock_ctx_with_guild.channel.send.assert_called_once_with(
      'hold on hold on, TestOpponent has to say $howdy to ol\' bungo first'
    )


@pytest.mark.asyncio
async def test_wager_opponent_in_guild_not_registered(mock_db, mock_ctx_with_guild, mock_bot):
  con, cur = mock_db

  creator_id = str(uuid.uuid4())
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (creator_id, 12345, 'TestCreator'))
  con.commit()

  mentioned_user = MagicMock()
  mentioned_user.id = 67890
  mentioned_user.display_name = 'testopponent'
  mock_ctx_with_guild.message.mentions = [mentioned_user]

  with patch('casino.bot.con', con), patch('casino.bot.bot', mock_bot):
    from casino.bot import wager

    await wager(mock_ctx_with_guild, 'testopponent', description='test bet')

    mock_ctx_with_guild.channel.send.assert_called_once_with(
      'hold on hold on, testopponent has to say $howdy to ol\' bungo first'
    )


@pytest.mark.asyncio
async def test_wager_opponent_not_in_guild(mock_db, mock_ctx_with_guild, mock_bot):
  con, cur = mock_db

  creator_id = str(uuid.uuid4())
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (creator_id, 12345, 'TestCreator'))
  con.commit()

  mentioned_user = MagicMock()
  mentioned_user.id = 99999
  mentioned_user.display_name = 'NoSuchPerson'
  mock_ctx_with_guild.message.mentions = [mentioned_user]

  with patch('casino.bot.con', con), patch('casino.bot.bot', mock_bot):
    from casino.bot import wager

    await wager(mock_ctx_with_guild, 'NoSuchPerson', description='test bet')

    mock_ctx_with_guild.channel.send.assert_called_once_with(
      'hold on hold on, NoSuchPerson has to say $howdy to ol\' bungo first'
    )


@pytest.mark.asyncio
async def test_wager_description_too_long(mock_db, mock_ctx_with_guild, mock_bot):
  con, cur = mock_db

  creator_id = str(uuid.uuid4())
  opponent_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (creator_id, 12345, 'TestCreator'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (opponent_id, 67890, 'TestOpponent'))
  con.commit()

  long_description = 'x' * 281

  with patch('casino.bot.con', con), patch('casino.bot.bot', mock_bot):
    from casino.bot import wager

    await wager(mock_ctx_with_guild, 'TestOpponent', description=long_description)

    mock_ctx_with_guild.channel.send.assert_called_once_with(
      'hold on partner that description\'s too long, keep it under 280 characters'
    )


@pytest.mark.asyncio
async def test_wager_bet_created_in_database(mock_db, mock_ctx_with_guild, mock_bot):
  con, cur = mock_db

  creator_id = str(uuid.uuid4())
  opponent_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (creator_id, 12345, 'TestCreator'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (opponent_id, 67890, 'TestOpponent'))
  con.commit()

  mentioned_user = MagicMock()
  mentioned_user.id = 67890
  mentioned_user.display_name = 'TestOpponent'
  mock_ctx_with_guild.message.mentions = [mentioned_user]

  with patch('casino.bot.con', con), patch('casino.bot.bot', mock_bot):
    from casino.bot import wager

    await wager(mock_ctx_with_guild, 'TestOpponent', description='Test Description')

    bet = cur.execute('SELECT * FROM bet WHERE id = 1').fetchone()
    assert bet is not None
    assert bet[0] == 1
    assert bet[1] == creator_id
    assert bet[2] == opponent_id
    assert bet[3] == 'Test Description'
    assert bet[5] == 'active'
    assert bet[7] == '12345'


@pytest.mark.asyncio
async def test_wager_bet_id_returned(mock_db, mock_ctx_with_guild, mock_bot):
  con, cur = mock_db

  creator_id = str(uuid.uuid4())
  opponent_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (creator_id, 12345, 'TestCreator'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (opponent_id, 67890, 'TestOpponent'))
  con.commit()

  mentioned_user = MagicMock()
  mentioned_user.id = 67890
  mentioned_user.display_name = 'TestOpponent'
  mock_ctx_with_guild.message.mentions = [mentioned_user]

  with patch('casino.bot.con', con), patch('casino.bot.bot', mock_bot):
    from casino.bot import wager

    await wager(mock_ctx_with_guild, 'TestOpponent', description='First bet')

    call_args = mock_ctx_with_guild.channel.send.call_args[0][0]
    assert 'alrighty your ticket is 101 good luck champ' == call_args


@pytest.mark.asyncio
async def test_wager_opponent_registered_not_in_guild(mock_db, mock_ctx_with_guild, mock_bot):
  con, cur = mock_db

  creator_id = str(uuid.uuid4())
  opponent_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (creator_id, 12345, 'TestCreator'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (opponent_id, 99999, 'GoneUser'))
  con.commit()

  mentioned_user = MagicMock()
  mentioned_user.id = 99999
  mentioned_user.display_name = 'GoneUser'
  mock_ctx_with_guild.message.mentions = [mentioned_user]

  with patch('casino.bot.con', con), patch('casino.bot.bot', mock_bot):
    from casino.bot import wager

    await wager(mock_ctx_with_guild, 'GoneUser', description='test bet')

    mock_ctx_with_guild.channel.send.assert_called_once()
    call_args = mock_ctx_with_guild.channel.send.call_args[0][0]
    assert 'alrighty your ticket is' in call_args

    bet = cur.execute('SELECT * FROM bet WHERE id = 1').fetchone()
    assert bet is not None
    assert bet[1] == creator_id
    assert bet[2] == opponent_id
