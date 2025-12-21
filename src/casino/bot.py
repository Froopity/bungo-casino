import os
import sqlite3
import sys
import uuid
from pathlib import Path

import discord
from discord.ext import commands
import dotenv


dotenv.load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$', intents=intents)

db_path = os.getenv('DATABASE_PATH', str((Path(__file__).parent.parent.parent / 'casino.db').resolve()))
con = sqlite3.connect(db_path)
cur = con.cursor()

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command()
async def slot(ctx):
  if ctx.author == bot.user:
    return

  if str(ctx.author.id) == '108455086367207424':
    await ctx.channel.send('u lost')
    return

  await ctx.channel.send('u win!')
  return


@bot.command()
async def howdy(ctx, display_name: str):
    if ctx.author == bot.user:
        return
    
    print(display_name)

    existing_user = cur.execute('SELECT display_name FROM user WHERE discord_id = ?', (ctx.author.id,)).fetchone()
    if existing_user:
        await ctx.channel.send(f'u already got a name: {existing_user[0]}')
        return

    if display_name is None or len(display_name) == 0:
        await ctx.channel.send('u gotta tell me ur name! say "$howdy <urname>"')
        return

    if len(display_name) > 32:
        await ctx.channel.send('i aint gonna remember all that, pick a shorter name')
        return

    if display_name == '@bungo' or display_name == '<@1450042419964809328>' or display_name in str(bot.user.id):
        await ctx.channel.send('fuckoffyoucunt')
        return

    if display_name.startswith('@'):
        await ctx.channel.send('think ur fucken cheeky huh')
        return

    if not display_name[0].isalnum():
        await ctx.channel.send('it gets weird when u start ur name with a symbol, try somethin else')
        return

    if not is_valid_name(display_name):
        await ctx.channel.send('nice try bingus, normal werds only in my casino (alphanumeric and !@#$%)')
        return

    name_taken = cur.execute('SELECT 1 FROM user WHERE display_name = ?', (display_name,)).fetchone()
    if name_taken:
        await ctx.channel.send(f'somebody already dang ol using the name {display_name}, get ur own')
        return

    cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)', (str(uuid.uuid4()), ctx.author.id, display_name))
    con.commit()
    await ctx.channel.send(f"why howdy {display_name}, welcome to ol' bungo's casino!")

def is_valid_name(text):
    allowed = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%')
    return all(char in allowed for char in text)

def format_ticket_id(db_id: int) -> int:
    """Convert database ID to display ticket number.
    Examples: 5 -> 105, 15 -> 115, 123 -> 1123"""
    return int(f"1{db_id:02d}")

def parse_ticket_id(display_id: int) -> int:
    """Convert display ticket number back to database ID.
    Examples: 105 -> 5, 115 -> 15, 1123 -> 123"""
    id_str = str(display_id)
    if not id_str.startswith('1') or len(id_str) < 3:
        raise ValueError(f"Invalid ticket number format: {display_id}")
    return int(id_str[1:])

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
    await ctx.channel.send("hold on partner that description's too long, keep it under 280 characters")
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
      await ctx.channel.send(f"hold on hold on, {mentioned_user.display_name} has to say $howdy to ol' bungo first")
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
        await ctx.channel.send(f"hold on hold on, ur pardner has to say $howdy to ol' bungo first")
        return

      opponent_id = opponent_user[0]
    else:
      matching_members = [
        m for m in ctx.guild.members
        if m.display_name.lower() == opponent.lower() or m.name.lower() == opponent.lower()
      ]

      if matching_members:
        await ctx.channel.send(f"hold on hold on, ur pardner has to say $howdy to ol' bungo first")
        return
      else:
        await ctx.channel.send(f"i ain't never heard o' no one with that name")
        return

  cur.execute(
    '''INSERT INTO bet
       (participant1_id, participant2_id, description, state, created_by_discord_id)
       VALUES (?, ?, ?, 'active', ?)''',
    (creator_id, opponent_id, description, str(ctx.author.id))
  )
  con.commit()

  bet_id = cur.lastrowid
  display_ticket_id = format_ticket_id(bet_id)

  await ctx.channel.send(f'alrighty your ticket is {display_ticket_id} good luck champ')


class ResolutionConfirmView(discord.ui.View):
  def __init__(self, bet_id: int, winner_id: str, winner_name: str, loser_name: str,
               resolver_discord_id: str, resolution_notes: str | None = None):
    super().__init__(timeout=60.0)
    self.bet_id = bet_id
    self.winner_id = winner_id
    self.winner_name = winner_name
    self.loser_name = loser_name
    self.resolver_discord_id = resolver_discord_id
    self.resolution_notes = resolution_notes

  @discord.ui.button(label='yes', style=discord.ButtonStyle.green)
  async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
    for item in self.children:
      item.disabled = True

    cur.execute(
      '''UPDATE bet
         SET state = 'resolved',
             resolved_at = CURRENT_TIMESTAMP,
             resolved_by_discord_id = ?,
             winner_id = ?,
             resolution_notes = ?
         WHERE id = ? AND state = 'active' ''',
      (self.resolver_discord_id, self.winner_id, self.resolution_notes, self.bet_id)
    )
    con.commit()

    if cur.rowcount == 0:
      bet = cur.execute('SELECT state FROM bet WHERE id = ?', (self.bet_id,)).fetchone()
      if bet and bet[0] != 'active':
        await interaction.response.edit_message(
          content="cmon champ, that wager's long gone by now",
          view=self
        )
      else:
        await interaction.response.edit_message(
          content='somethin went wrong there pardner',
          view=self
        )
      return

    await interaction.response.edit_message(
      content=f'congrertulatiorns {self.winner_name}, betrr luck next time {self.loser_name}',
      view=self
    )

  @discord.ui.button(label='nevrmind', style=discord.ButtonStyle.grey)
  async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
    for item in self.children:
      item.disabled = True

    await interaction.response.edit_message(
      content='alright pardner, resolution cancelled',
      view=self
    )


class CancellationConfirmView(discord.ui.View):
  def __init__(self, bet_id: int, canceller_discord_id: str):
    super().__init__(timeout=60.0)
    self.bet_id = bet_id
    self.canceller_discord_id = canceller_discord_id

  @discord.ui.button(label='yes', style=discord.ButtonStyle.green)
  async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
    for item in self.children:
      item.disabled = True

    cur.execute(
      '''UPDATE bet
         SET state = 'cancelled'
         WHERE id = ? AND state = 'active' ''',
      (self.bet_id,)
    )
    con.commit()

    if cur.rowcount == 0:
      bet = cur.execute('SELECT state FROM bet WHERE id = ?', (self.bet_id,)).fetchone()
      if bet and bet[0] != 'active':
        await interaction.response.edit_message(
          content="cmon champ, that wager's long gone by now",
          view=self
        )
      else:
        await interaction.response.edit_message(
          content='somethin went wrong there pardner',
          view=self
        )
      return

    await interaction.response.edit_message(
      content='ah well',
      view=self
    )

  @discord.ui.button(label='nevrmind', style=discord.ButtonStyle.grey)
  async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
    for item in self.children:
      item.disabled = True

    await interaction.response.edit_message(
      content='alright pardner, cancellation cancelled',
      view=self
    )


async def parse_winner_for_bet(ctx, winner_arg, participant1_id, participant2_id, cur):
  winner_id = None
  winner_discord_id = None

  if ctx.message.mentions:
    mentioned_user = ctx.message.mentions[0]
    winner_discord_id = str(mentioned_user.id)

    winner_user = cur.execute(
      'SELECT id FROM user WHERE discord_id = ?',
      (winner_discord_id,)
    ).fetchone()

    if winner_user:
      winner_id = winner_user[0]
  else:
    winner_user = cur.execute(
      'SELECT id, discord_id FROM user WHERE LOWER(display_name) = LOWER(?)',
      (winner_arg,)
    ).fetchone()

    if winner_user:
      winner_id = winner_user[0]
      winner_discord_id = winner_user[1]
    else:
      matching_members = [
        m for m in ctx.guild.members
        if m.display_name.lower() == winner_arg.lower() or m.name.lower() == winner_arg.lower()
      ]

      if matching_members:
        member = matching_members[0]
        winner_discord_id = str(member.id)

        winner_user = cur.execute(
          'SELECT id FROM user WHERE discord_id = ?',
          (winner_discord_id,)
        ).fetchone()

        if winner_user:
          winner_id = winner_user[0]

  if not winner_id or winner_id not in (participant1_id, participant2_id):
    p1_name = cur.execute(
      'SELECT display_name FROM user WHERE id = ?',
      (participant1_id,)
    ).fetchone()[0]

    p2_name = cur.execute(
      'SELECT display_name FROM user WHERE id = ?',
      (participant2_id,)
    ).fetchone()[0]

    return None, f'they aint a pard of this, its between {p1_name} and {p2_name}', None

  all_participant_names = cur.execute(
    'SELECT id, display_name FROM user WHERE id IN (?, ?)',
    (participant1_id, participant2_id)
  ).fetchall()

  winner_name = None
  loser_name = None

  for pid, pname in all_participant_names:
    if pid == winner_id:
      winner_name = pname
    else:
      loser_name = pname

  return winner_id, winner_name, loser_name


@bot.command()
async def resolve(ctx, display_bet_id: int, winner: str, *, notes: str = ''):
  if ctx.author == bot.user:
    return

  resolver = cur.execute(
    'SELECT id FROM user WHERE discord_id = ?',
    (str(ctx.author.id),)
  ).fetchone()

  if not resolver:
    await ctx.channel.send('woaah slow down ther cowboy, you gotta say $howdy first')
    return

  resolver_id = resolver[0]

  try:
    bet_id = parse_ticket_id(display_bet_id)
  except ValueError:
    await ctx.channel.send("that don't look like a proper ticket numbr")
    return

  bet = cur.execute('SELECT * FROM bet WHERE id = ?', (bet_id,)).fetchone()

  if not bet:
    await ctx.channel.send("i ain't know nothin bout that ticket numbr")
    return

  if bet[5] != 'active':
    await ctx.channel.send("cmon champ, that wager's long gone by now")
    return

  participant1_id = bet[1]
  participant2_id = bet[2]

  if resolver_id not in (participant1_id, participant2_id):
    await ctx.channel.send("slow down pardner, you ain't a part of that there wager")
    return

  winner_id, result, loser_name = await parse_winner_for_bet(ctx, winner, participant1_id, participant2_id, cur)

  if not winner_id:
    await ctx.channel.send(result)
    return

  winner_name = result
  bet_description = bet[3]

  resolution_notes = None
  if notes:
    if notes.startswith('notes:'):
      resolution_notes = notes[6:].strip()
    else:
      resolution_notes = notes

    if len(resolution_notes) > 280:
      await ctx.channel.send('keep them notes under 280 characters pardner')
      return

  view = ResolutionConfirmView(
    bet_id=bet_id,
    winner_id=winner_id,
    winner_name=winner_name,
    loser_name=loser_name,
    resolver_discord_id=str(ctx.author.id),
    resolution_notes=resolution_notes
  )

  confirmation_msg = (
    f"wager: {bet_description}\n"
    f"between: {winner_name} and {loser_name}\n\n"
    f"r ya sure {winner_name} wins?"
  )

  await ctx.channel.send(confirmation_msg, view=view)


@bot.command()
async def cancel(ctx, display_bet_id: int):
  if ctx.author == bot.user:
    return

  canceller = cur.execute(
    'SELECT id FROM user WHERE discord_id = ?',
    (str(ctx.author.id),)
  ).fetchone()

  if not canceller:
    await ctx.channel.send('woaah slow down ther cowboy, you gotta say $howdy first')
    return

  canceller_id = canceller[0]

  try:
    bet_id = parse_ticket_id(display_bet_id)
  except ValueError:
    await ctx.channel.send("that don't look like a proper ticket numbr")
    return

  bet = cur.execute('SELECT * FROM bet WHERE id = ?', (bet_id,)).fetchone()

  if not bet:
    await ctx.channel.send("i ain't know nothin bout that ticket numbr")
    return

  if bet[5] != 'active':
    await ctx.channel.send("cmon champ, that wager's long gone by now")
    return

  participant1_id = bet[1]
  participant2_id = bet[2]

  if canceller_id not in (participant1_id, participant2_id):
    await ctx.channel.send("slow down pardner, you ain't a part of that there wager")
    return

  view = CancellationConfirmView(
    bet_id=bet_id,
    canceller_discord_id=str(ctx.author.id)
  )

  await ctx.channel.send('r ya sure?', view=view)


@bot.command()
async def tickets(ctx):
  if ctx.author == bot.user:
    return

  user = cur.execute(
    'SELECT id, display_name FROM user WHERE discord_id = ?',
    (str(ctx.author.id),)
  ).fetchone()

  if not user:
    await ctx.channel.send('woaah slow down ther cowboy, you gotta say $howdy first')
    return

  user_id = user[0]

  query = '''
    SELECT
      b.id,
      b.description,
      u1.display_name as p1_name,
      u2.display_name as p2_name,
      b.created_at
    FROM bet b
    JOIN user u1 ON b.participant1_id = u1.id
    JOIN user u2 ON b.participant2_id = u2.id
    WHERE (b.participant1_id = ? OR b.participant2_id = ?)
      AND b.state = 'active'
    ORDER BY b.created_at DESC
  '''

  tickets = cur.execute(query, (user_id, user_id)).fetchall()

  if not tickets:
    await ctx.channel.send("u ain't got no active wagers right now pardner")
    return

  lines = ['```', 'ur active tickets', '━━━━━━━━━━━━━━━━━━━━━━━']

  for ticket_id, description, p1_name, p2_name, created_at in tickets:
    display_ticket_id = format_ticket_id(ticket_id)
    desc_display = description[:40] + '...' if len(description) > 40 else description
    lines.append(f'#{display_ticket_id}: {desc_display}')
    lines.append(f'  between {p1_name} and {p2_name}')
    lines.append('')

  lines.append('━━━━━━━━━━━━━━━━━━━━━━━')
  lines.append('```')

  await ctx.channel.send('\n'.join(lines))


@bot.command(aliases=['leaderboard'])
async def leadrbord(ctx):
  if ctx.author == bot.user:
    return

  query = '''
    WITH user_stats AS (
      SELECT
        u.id,
        u.display_name,
        SUM(CASE WHEN b.winner_id = u.id THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN b.winner_id = u.id THEN 1
                 WHEN (b.participant1_id = u.id OR b.participant2_id = u.id)
                      AND b.winner_id IS NOT NULL
                      AND b.winner_id != u.id THEN -1
                 ELSE 0 END) AS balance
      FROM user u
      LEFT JOIN bet b ON (b.participant1_id = u.id OR b.participant2_id = u.id)
                      AND b.state = 'resolved'
      GROUP BY u.id, u.display_name
      HAVING COUNT(CASE WHEN b.state = 'resolved' THEN 1 END) > 0
    )
    SELECT display_name, balance, wins
    FROM user_stats
    ORDER BY balance DESC, wins DESC
    LIMIT 10
  '''

  results = cur.execute(query).fetchall()

  if not results:
    await ctx.channel.send("ain't nobody played yet pardner")
    return

  lines = ['```', "big bungo's leadrbord", '━━━━━━━━━━━━━━━━━━━━━━━']

  for idx, (name, balance, wins) in enumerate(results, 1):
    display_name = name[:15] + '...' if len(name) > 15 else name

    if balance >= 0:
      balance_str = f'${balance}'
    else:
      balance_str = f'-${abs(balance)}'

    rank_str = f'#{idx}'.ljust(4)
    name_str = display_name.ljust(18)
    balance_str = balance_str.rjust(6)
    wins_str = f'({wins}W)'

    lines.append(f'{rank_str}{name_str}{balance_str}  {wins_str}')

  lines.append('━━━━━━━━━━━━━━━━━━━━━━━')
  lines.append('```')

  await ctx.channel.send('\n'.join(lines))


if __name__ == '__main__':
    bot_token = os.getenv('DISCORD_BOT_TOKEN')
    if bot_token is None:
      print('Discord API token not found')
      sys.exit(1)

    bot.run(bot_token)
