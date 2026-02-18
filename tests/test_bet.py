import uuid
from unittest.mock import MagicMock

import pytest

from casino.model.bet import Bet


def make_row(state='active', p1=None, p2=None):
  p1 = p1 or str(uuid.uuid4())
  p2 = p2 or str(uuid.uuid4())
  return (1, p1, p2, 'test description', '', state,
          '2024-01-01', 'creator_discord', None, None, None, None)


def test_from_row_creates_bet():
  row = make_row()
  bet = Bet.from_row(row)
  assert bet.id == 1
  assert bet.description == 'test description'
  assert bet.state == 'active'


def test_from_row_none_raises():
  with pytest.raises(ValueError):
    Bet.from_row(None)


def test_is_active_true():
  bet = Bet.from_row(make_row(state='active'))
  assert bet.is_active is True


def test_is_active_false():
  bet = Bet.from_row(make_row(state='resolved'))
  assert bet.is_active is False


def test_participants_returns_both_users(mock_db):
  con, cur = mock_db

  p1_id = str(uuid.uuid4())
  p2_id = str(uuid.uuid4())

  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p1_id, 11111, 'Alice'))
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (p2_id, 22222, 'Bob'))
  con.commit()

  bet = Bet.from_row(make_row(p1=p1_id, p2=p2_id))
  p1, p2 = bet.participants(con)

  assert p1.display_name == 'Alice'
  assert p2.display_name == 'Bob'
