import uuid
from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_howdy_creates_new_user(mock_db, mock_ctx):
  con, cur = mock_db

  with patch('casino.bot.con', con), patch('casino.bot.bot') as mock_bot:
    mock_bot.user.id = 999999
    from casino.bot import howdy

    await howdy(mock_ctx, 'TestUser')

    mock_ctx.channel.send.assert_called_once_with("why howdy TestUser, welcome to ol' bungo's casino!")

    result = cur.execute('SELECT display_name FROM user WHERE discord_id = ?', (12345,)).fetchone()
    assert result is not None
    assert result[0] == 'TestUser'


@pytest.mark.asyncio
async def test_howdy_rejects_existing_user(mock_db, mock_ctx):
  con, cur = mock_db
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (str(uuid.uuid4()), 12345, 'ExistingUser'))
  con.commit()

  with patch('casino.bot.con', con), patch('casino.bot.bot') as mock_bot:
    mock_bot.user.id = 999999
    from casino.bot import howdy

    await howdy(mock_ctx, 'NewName')

    mock_ctx.channel.send.assert_called_once_with('u already got a name: ExistingUser')


@pytest.mark.asyncio
async def test_howdy_rejects_taken_display_name(mock_db, mock_ctx):
  con, cur = mock_db
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (str(uuid.uuid4()), 99999, 'TakenName'))
  con.commit()

  with patch('casino.bot.con', con), patch('casino.bot.bot') as mock_bot:
    mock_bot.user.id = 999999
    from casino.bot import howdy

    await howdy(mock_ctx, 'TakenName')

    mock_ctx.channel.send.assert_called_once_with('somebody already dang ol using the name TakenName, get ur own')
