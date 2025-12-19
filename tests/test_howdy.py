import sqlite3
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_db():
  con = sqlite3.connect(':memory:')
  cur = con.cursor()
  cur.execute('''
    CREATE TABLE user (
      id TEXT PRIMARY KEY,
      discord_id INTEGER,
      display_name TEXT
    )
  ''')
  con.commit()
  return con, cur


@pytest.fixture
def mock_ctx():
  ctx = MagicMock()
  ctx.author = MagicMock()
  ctx.author.id = 12345
  ctx.channel = MagicMock()
  ctx.channel.send = AsyncMock()
  return ctx


@pytest.mark.asyncio
async def test_howdy_creates_new_user(mock_db, mock_ctx):
  con, cur = mock_db

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
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

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import howdy

    await howdy(mock_ctx, 'NewName')

    mock_ctx.channel.send.assert_called_once_with('u already got a name: ExistingUser')


@pytest.mark.asyncio
async def test_howdy_rejects_taken_display_name(mock_db, mock_ctx):
  con, cur = mock_db
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (str(uuid.uuid4()), 99999, 'TakenName'))
  con.commit()

  with patch('casino.bot.cur', cur), patch('casino.bot.con', con):
    from casino.bot import howdy

    await howdy(mock_ctx, 'TakenName')

    mock_ctx.channel.send.assert_called_once_with('somebody already dang ol using the name TakenName, get ur own')
