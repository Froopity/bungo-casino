from typing import TypeGuard
from discord.ui import Item, Button


def is_button(item: Item) -> TypeGuard[Button]:
  return isinstance(item, Button)
