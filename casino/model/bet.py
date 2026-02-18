from __future__ import annotations

from sqlite3 import Row, Connection
from dataclasses import dataclass
from datetime import datetime
from casino.model.user import User, find_ids

@dataclass(frozen=True)
class Bet:
  id: int
  participant1_id: str
  participant2_id: str
  description: str
  details: str
  state: str
  created_at: datetime
  created_by_discord_id: str
  resolved_at: datetime
  resolved_by_discord_id: str
  winner_id: str
  resolution_notes: str

  @classmethod
  def from_row(cls, row: Row | None) -> Bet:
    if row is None:
      raise ValueError('No row provided to create bet from')
    return cls(*row)

  @property
  def is_active(self):
    return self.state == 'active'

  def participants(self, con: Connection) -> tuple[User, User]:
    participants = find_ids([self.participant1_id, self.participant2_id], con)

    return participants[self.participant1_id], participants[self.participant2_id]
