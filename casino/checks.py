import functools
from discord.ext import commands


class NotRegisteredError(commands.CheckFailure):
  pass


def ignore_bots(func):
  @functools.wraps(func)
  async def wrapper(ctx, *args, **kwargs):
    if ctx.author == ctx.bot.user:
      return
    return await func(ctx, *args, **kwargs)
  return wrapper


def is_registered(cur):
  async def predicate(ctx):
    user = cur.execute(
      'SELECT id FROM user WHERE discord_id = ?',
      (str(ctx.author.id),)
    ).fetchone()
    if not user:
      raise NotRegisteredError()
    return True
  return commands.check(predicate)
