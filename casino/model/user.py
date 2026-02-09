from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass
import sqlite3

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
    return cls(**dict(row))
