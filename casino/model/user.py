from __future__ import annotations

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


def get_discord_user(user: DiscordUser, con: sqlite3.Connection) -> User:
  discord_id = str(user.id)

  row = con.execute(
    'SELECT * FROM user WHERE discord_id = ?',
    (discord_id,)
  ).fetchone()

  if not row:
    raise UnknownEntityError(user.name)

  return User.from_row(row)


def get_users_by_id(user_ids: list[int], con: sqlite3.Connection) -> dict[int, User]:
  placeholders = ', '.join(['?'] * len(user_ids))

  users = {}
  for row in con.execute(f'select * from user where id in ({placeholders})', user_ids):
    user = User.from_row(row)
    users[user.id] = user

  return users
