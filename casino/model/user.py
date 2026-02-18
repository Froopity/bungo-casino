from __future__ import annotations
from discord import Member
from sqlite3 import Connection

from datetime import datetime
from dataclasses import dataclass
from discord.abc import User as DiscordUser
import sqlite3

from casino.exceptions import UnknownEntityError

@dataclass(frozen=True)
class User:
  id: str
  discord_id: str
  display_name: str
  created_at: datetime
  bungo_dollars: int
  bungo_bux: int
  spins: int

  @classmethod
  def from_row(cls, row: sqlite3.Row) -> User:
    return cls(*row)


def from_discord_user(user: DiscordUser | Member, con: sqlite3.Connection) -> User:
  discord_id = str(user.id)

  row = con.execute(
    'SELECT * FROM user WHERE discord_id = ?',
    (discord_id,)
  ).fetchone()

  if not row:
    raise UnknownEntityError(user.name)

  return User.from_row(row)


def find_ids(user_ids: list[str], con: Connection) -> dict[str, User]:
  placeholders = ', '.join(['?'] * len(user_ids))

  users: dict[str, User] = {}
  for row in con.execute(f'select * from user where id in ({placeholders})', user_ids):
    user: User = User.from_row(row)
    users[user.id] = user

  return users

def with_name_exists(name: str, con: Connection) -> bool:
  return con.execute('SELECT 1 FROM user WHERE display_name = ?', (name,)).fetchone() is not None
