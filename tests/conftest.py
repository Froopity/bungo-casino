import sys
import sqlite3
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

_MIGRATIONS_DIR = Path(__file__).parent.parent / 'migrations'
_MIGRATION_SQL = None

def _load_migrations():
  global _MIGRATION_SQL
  if _MIGRATION_SQL is not None:
    return _MIGRATION_SQL
  sql_files = sorted(_MIGRATIONS_DIR.glob('*.sql'))
  parts = []
  for f in sql_files:
    text = f.read_text()
    lines = [l for l in text.splitlines() if not l.startswith('-- ')]
    parts.append('\n'.join(lines))
  _MIGRATION_SQL = '\n'.join(parts)
  return _MIGRATION_SQL


@pytest.fixture
def mock_db():
  con = sqlite3.connect(':memory:')
  con.executescript(_load_migrations())
  cur = con.cursor()

  yield con, cur

  con.close()


@pytest.fixture
def mock_ctx():
  ctx = MagicMock()
  ctx.author = MagicMock()
  ctx.author.id = 12345
  ctx.channel = MagicMock()
  ctx.channel.send = AsyncMock()
  ctx.message = MagicMock()
  ctx.message.mentions = []
  return ctx


@pytest.fixture
def mock_ctx_with_guild():
  ctx = MagicMock()
  ctx.author = MagicMock()
  ctx.author.id = 12345
  ctx.channel = MagicMock()
  ctx.channel.send = AsyncMock()
  ctx.message = MagicMock()
  ctx.message.mentions = []

  ctx.guild = MagicMock()
  mock_member1 = MagicMock()
  mock_member1.id = 12345
  mock_member1.display_name = 'TestCreator'
  mock_member1.name = 'testcreator'

  mock_member2 = MagicMock()
  mock_member2.id = 67890
  mock_member2.display_name = 'TestOpponent'
  mock_member2.name = 'testopponent'

  ctx.guild.members = [mock_member1, mock_member2]
  ctx.guild.get_member = lambda member_id: mock_member2 if member_id == 67890 else mock_member1 if member_id == 12345 else None

  return ctx


@pytest.fixture
def mock_interaction():
  interaction = MagicMock()
  interaction.response = MagicMock()
  interaction.response.edit_message = AsyncMock()
  interaction.response.send_message = AsyncMock()
  interaction.user = MagicMock()
  interaction.user.id = 12345
  return interaction


@pytest.fixture
def mock_bot():
  bot = MagicMock()
  bot.user = MagicMock()
  bot.user.id = 999999
  return bot
