import os
import sqlite3
import sys
import uuid
import random
from pathlib import Path

import discord
from discord.ext import commands
import dotenv

from casino.slots import spin_slots
from casino.utils import is_valid_name, format_ticket_id, parse_ticket_id

random.seed()
dotenv.load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$', intents=intents, help_command=None)

db_path = os.getenv('DATABASE_PATH', str((Path(__file__).parent.parent / 'data' / 'casino.db').resolve()))
con = sqlite3.connect(db_path)
cur = con.cursor()

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


@bot.command(help='test ur luck! remember, taran always loses')
async def spin(ctx):
  if ctx.author == bot.user:
    return

  gambler = cur.execute(
    'SELECT id, display_name, spins, bungo_bux FROM user WHERE discord_id = ?',
    (str(ctx.author.id),)
  ).fetchone()

  if not gambler:
    await ctx.channel.send('woaah slow down ther cowboy, you gotta say $howdy first')
    return

  user_id, name, spins, bungo_bux = gambler

  if spins == 0:
    await ctx.channel.send(f'sorry {name}, but ur outta spins. come back when u get one over on ur buds')
    return

  frame, bux = spin_slots()
  msg = f'''```\n{frame}\n```'''

  cur.execute('UPDATE user SET spins = ?, bungo_bux = ? WHERE discord_id = ?', (spins - 1, bungo_bux + bux, str(ctx.author.id)))

  if bux == 0:
    msg += 'u lost\n'
  else:
    msg += f'u win {bux} bungo bux, congrats high roller!\n'

  cur.execute('INSERT INTO spins (user_id, winnings) VALUES (?, ?)',
              (user_id, bux))

  con.commit()
  if spins > 1:
    msg += f'come back soon ya hear? you got {spins - 1} spins left!'
  else:
    msg += 'ur all outta spins now champ!'
  await ctx.channel.send(msg)


@bot.command(help='introduce urself, pick a name and don\'t try any funny business')
async def howdy(ctx, display_name: str | None):
    if ctx.author == bot.user:
        return

    existing_user = cur.execute('SELECT display_name FROM user WHERE discord_id = ?', (ctx.author.id,)).fetchone()
    if existing_user:
        name = existing_user[0]
        if display_name is None:
          await ctx.channel.send(f'howdy {name}, try placing a bet!')
        else:
          await ctx.channel.send(f'u already got a name: {name}')
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


@bot.command(help='already figured that one out, huh? helps, duh')
async def help(ctx):
  lines = [
      '```'
      "new around here pardner? let's help get ya situated real fast like:",
      "i don't know how's it works were ur from, but here? we all start our conversations with '$'",
      "introduce yourself, if'n you ain't already, through $howdy, and then get tryin' with these other commands:\n"
  ]
  for command in bot.commands:
      if command.name != 'howdy':
        lines.append(f'{command.name}')
        lines.append(f' - {command.help}\n')

  lines.append('```')
  await ctx.channel.send(f'{'\n'.join(lines)}')

@bot.command(help='place a bet, make sure u tag ur opponent using @<discord_name>, and then add a description of y\'alls wager')
async def wager(ctx, opponent: str | None = None, *, description: str | None = None):
  if ctx.author == bot.user:
    return

  if opponent is None:
      await ctx.channel.send('u gotta pick an opponent champ!')
      return
  if description is None:
    await ctx.channel.send('u gotta describe ur wager')
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
      await ctx.channel.send('u gotta tag ur opponent like this: $wager @bungo ...')
      return

  cur.execute(
    '''INSERT INTO bet
       (participant1_id, participant2_id, description, state, created_by_discord_id)
       VALUES (?, ?, ?, 'active', ?)''',
    (creator_id, opponent_id, description, str(ctx.author.id))
  )
  con.commit()

  await ctx.channel.send(f'alrighty your ticket is {format_ticket_id(cur.lastrowid)} good luck champ')


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

    # Get loser_id to update their bungo dollars
    bet = cur.execute('SELECT participant1_id, participant2_id FROM bet WHERE id = ?', (self.bet_id,)).fetchone()
    loser_id = bet[0] if bet[1] == self.winner_id else bet[1]

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
    cur.execute('UPDATE user SET spins = spins + 1, bungo_dollars = bungo_dollars + 1 WHERE id = ?', (self.winner_id,))
    cur.execute('UPDATE user SET bungo_dollars = bungo_dollars - 1 WHERE id = ?', (loser_id,))
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


@bot.command(help='bet\'s all done? well then, better let me know who won! show me ur ticket and ur winner, and i\'ll put it up on that thar leadrbord')
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


@bot.command(help='bet not work out? just let me know the ticket number and i\'ll take it offa my books', aliases=['rules'])
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


@bot.command(help='forgot ur ticket number eh? that\'s okay, i got \'em all up here, just ask and i\'ll give ya the full list of active bets')
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
    created_date = created_at.split()[0] if created_at else ''
    lines.append(f'#{display_ticket_id}: {description}')
    lines.append(f'  between {p1_name} and {p2_name}')
    lines.append(f'  created: {created_date}')
    lines.append('')

  lines.append('━━━━━━━━━━━━━━━━━━━━━━━')
  lines.append('```')

  await ctx.channel.send('\n'.join(lines))


@bot.command(help='check ur holdings - bungo dollars, bungo bux, and spins')
async def wallet(ctx):
  if ctx.author == bot.user:
    return

  user = cur.execute(
    'SELECT display_name, bungo_dollars, bungo_bux, spins FROM user WHERE discord_id = ?',
    (str(ctx.author.id),)
  ).fetchone()

  if not user:
    await ctx.channel.send('woaah slow down ther cowboy, you gotta say $howdy first')
    return

  display_name, bungo_dollars, bungo_bux, spins = user

  lines = ['```', f"{display_name}'s wallet", '━━━━━━━━━━━━━━━━━━━━━━━']

  if bungo_dollars >= 0:
    dollars_str = f'${bungo_dollars}'
  else:
    dollars_str = f'-${abs(bungo_dollars)}'

  lines.append(f'bungo dollars: {dollars_str}')
  lines.append(f'bungo bux:     {bungo_bux}')
  lines.append(f'spins:         {spins}')
  lines.append('━━━━━━━━━━━━━━━━━━━━━━━')
  lines.append('```')

  await ctx.channel.send('\n'.join(lines))


@bot.command(aliases=['leaderboard'], help='i can tell ya who\'s the better better outta u \'n ur buds')
async def leadrbord(ctx):
  if ctx.author == bot.user:
    return

  query = '''
    WITH user_stats AS (
      SELECT
        u.display_name,
        u.bungo_dollars AS balance,
        SUM(CASE WHEN b.winner_id = u.id THEN 1 ELSE 0 END) AS wins
      FROM user u
      LEFT JOIN bet b ON (b.participant1_id = u.id OR b.participant2_id = u.id)
                      AND b.state = 'resolved'
                      AND b.winner_id = u.id
      GROUP BY u.id, u.display_name, u.bungo_dollars
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
