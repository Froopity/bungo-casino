import sys
import sqlite3
import uuid
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from yoyo import read_migrations, get_backend

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_db():
  with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
    db_path = tmp.name

  backend = get_backend(f'sqlite:///{db_path}')

  migrations_path = Path(__file__).parent.parent / 'migrations'
  migrations = read_migrations(str(migrations_path))

  with backend.lock():
    backend.apply_migrations(backend.to_apply(migrations))

  con = backend.connection
  cur = con.cursor()

  yield con, cur

  con.close()
  Path(db_path).unlink(missing_ok=True)


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
