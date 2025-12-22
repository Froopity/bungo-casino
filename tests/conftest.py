import sys
import sqlite3
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


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
  cur.execute('''
    CREATE TABLE bet (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      participant1_id TEXT NOT NULL,
      participant2_id TEXT NOT NULL,
      description TEXT NOT NULL,
      details TEXT NULL,
      state TEXT NOT NULL DEFAULT 'active',
      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      created_by_discord_id TEXT NOT NULL,
      resolved_at TIMESTAMP NULL,
      resolved_by_discord_id TEXT NULL,
      winner_id TEXT NULL,
      resolution_notes TEXT NULL
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
