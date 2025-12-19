import os
import sqlite3
import uuid
from pathlib import Path

import discord
from discord.ext import commands
import dotenv


dotenv.load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$', intents=intents)

db_path = (Path(__file__).parent.parent / 'casino.db').resolve()
con = sqlite3.connect(db_path)
cur = con.cursor()

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


@bot.command()
async def howdy(ctx, display_name: str):
    if ctx.author == bot.user:
        return

    existing_user = cur.execute('SELECT display_name FROM user WHERE discord_id = ?', (ctx.author.id,)).fetchone()
    if existing_user:
        await ctx.channel.send(f'u already got a name: {existing_user[0]}')
        return

    name_taken = cur.execute('SELECT 1 FROM user WHERE display_name = ?', (display_name,)).fetchone()
    if name_taken:
        await ctx.channel.send(f'somebody already dang ol using the name {display_name}, get ur own')
        return

    cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)', (str(uuid.uuid4()), ctx.author.id, display_name))
    con.commit()
    await ctx.channel.send(f"why howdy {display_name}, welcome to ol' bungo's casino!")


@bot.command()
async def wager(ctx, opponent: str, *, description: str):
  if ctx.author == bot.user:
    return

  creator = cur.execute(
    'SELECT id, display_name FROM user WHERE discord_id = ?',
    (str(ctx.author.id),)
  ).fetchone()

  if not creator:
    await ctx.channel.send('woaah slow down ther cowboy, you gotta say $howdy first')
    return

  creator_id, creator_name = creator

  if len(description) > 280:
    await ctx.channel.send('hold on partner that description\'s too long, keep it under 280 characters')
    return

  if ctx.message.mentions:
    mentioned_user = ctx.message.mentions[0]

    if mentioned_user.id == ctx.author.id:
      await ctx.channel.send('you cant place a wager on urself!')
      return

    opponent_user = cur.execute(
      'SELECT id FROM user WHERE discord_id = ?',
      (str(mentioned_user.id),)
    ).fetchone()

    if not opponent_user:
      await ctx.channel.send(f'hold on hold on, {mentioned_user.display_name} has to say $howdy to ol\' bungo first')
      return

    opponent_id = opponent_user[0]

  else:
    if opponent.lower() == creator_name.lower():
      await ctx.channel.send('you cant place a wager on urself!')
      return

    opponent_user = cur.execute(
      'SELECT id, discord_id FROM user WHERE display_name = ?',
      (opponent,)
    ).fetchone()

    if opponent_user:
      guild_member = ctx.guild.get_member(int(opponent_user[1]))

      if not guild_member:
        await ctx.channel.send(f'hold on hold on, {opponent} has to say $howdy to ol\' bungo first')
        return

      opponent_id = opponent_user[0]
    else:
      matching_members = [
        m for m in ctx.guild.members
        if m.display_name.lower() == opponent.lower() or m.name.lower() == opponent.lower()
      ]

      if matching_members:
        await ctx.channel.send(f'hold on hold on, {opponent} has to say $howdy to ol\' bungo first')
        return
      else:
        await ctx.channel.send(f'i ain\'t never heard o\' no {opponent}')
        return

  cur.execute(
    '''INSERT INTO bet
       (participant1_id, participant2_id, description, state, created_by_discord_id)
       VALUES (?, ?, ?, 'active', ?)''',
    (creator_id, opponent_id, description, str(ctx.author.id))
  )
  con.commit()

  bet_id = cur.lastrowid

  await ctx.channel.send(f'alrighty your ticket is {bet_id} good luck champ')


if __name__ == '__main__':
    bot.run(os.getenv('DISCORD_BOT_TOKEN'))
