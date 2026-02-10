from sqlite3 import Cursor, Row
from typing import Callable
import os
import random
import sqlite3
import sys
import uuid
from pathlib import Path

import discord
from discord.ext.commands.context import Context
import dotenv
from discord.ext import commands

from casino import sqlite_adapters
from casino.checks import ignore_bots, is_registered
from casino.exceptions import BungoError, SqlError, UnknownEntityError
from casino.model import user
from casino.model.user import User
from casino.slots import spin_slots
from casino.utils import get_bot_id, is_valid_name, format_ticket_id, parse_ticket_id, find_winner, name_is_bungo, calculate_global_debts, generate_debt_graph_image
from casino.views.cancellation_confirm import CancellationConfirmView
from casino.views.resolution_confirm import ResolutionConfirmView

random.seed()
dotenv.load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$', intents=intents, help_command=None)

sqlite_adapters.register_adapters()
db_path = os.getenv('DATABASE_PATH', str((Path(__file__).parent.parent / 'data' / 'casino.db').resolve()))
con = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)


@bot.event
async def on_ready():
  print(f'We have logged in as {bot.user}')


@bot.event
async def on_command_error(ctx, error):
  from casino.checks import NotRegisteredError
  if isinstance(error, NotRegisteredError):
    await ctx.channel.send('woaah slow down ther cowboy, you gotta say $howdy first')
  elif not isinstance(error, commands.CheckFailure):
    raise error


@bot.command(help='test ur luck! remember, taran always loses')
@ignore_bots
@is_registered(con)
async def spin(ctx: Context):
  gambler: User = user.from_discord_user(ctx.author, con)

  if gambler.spins == 0:
    await ctx.channel.send(f'sorry {gambler.display_name}, but ur outta spins. come back when u get one over on ur buds')
    return

  frame, bux = spin_slots()
  msg = f'''```\n{frame}\n```'''

  con.execute('UPDATE user SET spins = ?, bungo_bux = ? WHERE discord_id = ?',
              (gambler.spins - 1, gambler.bungo_bux + bux, str(ctx.author.id)))

  if bux == 0:
    msg += 'u lost\n'
  elif bux == 12:
    msg += 'well howwwdyyyy you hit the **bungo jackpot**! you get **12** bungo bux!\n'
  else:
    msg += f'u win **{bux}** bungo bux, congrats high roller!\n'

  con.execute('INSERT INTO spins (user_id, winnings) VALUES (?, ?)',
              (gambler.id, bux))

  con.commit()
  if gambler.spins > 1:
    msg += f'come back soon ya hear? you got **{gambler.spins - 1} spins left**!'
  else:
    msg += 'ur all outta spins now champ!'
  await ctx.channel.send(msg)


@bot.command(help="introduce urself, pick a name and don't try any funny business")
@ignore_bots
async def howdy(ctx: Context, display_name: str | None = None):
  try:
    existing_user: User = user.from_discord_user(ctx.author, con)
    if display_name is None:
      await ctx.channel.send(f'howdy {existing_user.display_name}, try placing a bet!')
    else:
      await ctx.channel.send(f'u already got a name: {existing_user.display_name}')
    return
  except UnknownEntityError:
    pass

  validations: list[tuple[Callable[[str | None], bool], str]] = [
      (lambda x: not x, 'u gotta tell me ur name! say "$howdy <urname>"'),
      (lambda x: len(x or '') > 32, 'i aint gonna remember all that, pick a shorter name'),
      (lambda x: name_is_bungo(x, get_bot_id(bot)), 'frick off'),
      (lambda x: x == '@everyone', 'think ur frickin cheeky huh'),
      (lambda x: x and not x[0].isalnum(), 'it gets weird when u start ur name with a symbol'),
      (lambda x: not is_valid_name(x), 'nice try bingus, normal werds only')
  ]

  # Use next() with a default of None to find the first failure
  error_msg: str | None = next((msg for check, msg in validations if check(display_name)), None)

  if error_msg:
      await ctx.channel.send(error_msg)
      return

  assert display_name is not None

  if user.with_name_exists(display_name, con):
    await ctx.channel.send(f'somebody already dang ol using the name {display_name}, get ur own')
    return

  con.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              (str(uuid.uuid4()), ctx.author.id, display_name))
  con.commit()
  await ctx.channel.send(f"why howdy {display_name}, welcome to ol' bungo's casino!")


@bot.command(help='already figured that one out, huh? helps, duh')
async def help(ctx):
  lines: list[str] = [
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


@bot.command(
  help="place a bet, make sure u tag ur opponent using @<discord_name>, and then add a description of y'alls wager")
@ignore_bots
@is_registered(con)
async def wager(ctx: Context, opponent_name: str | None = None, *, description: str | None = None):
  try:
    if not ctx.message.mentions or opponent_name is None:
      raise BungoError('u gotta tag ur opponent like this: $wager @bungo ...')

    if description is None:
      raise BungoError('u gotta describe ur wager')

    if name_is_bungo(opponent_name, get_bot_id(bot)):
      raise BungoError('u dont wanna play against the house bucko, bungo always wins')

    # Creator is already verified with @is_registered
    creator: User = user.from_discord_user(ctx.author, con)

    try:
      opponent: User = user.from_discord_user(ctx.message.mentions[0], con)
    except UnknownEntityError:
      raise BungoError(f"hold on hold on, {opponent.display_name} has to say $howdy to ol' bungo first")

    if opponent == creator:
      raise BungoError('you cant place a wager on urself!')

    if len(description) > 280:
      raise BungoError("hold on partner that description's too long, keep it under 280 characters")
  except BungoError as e:
    print(f'Encountered validation error: {e}')
    await ctx.channel.send(str(e))
    return

  cur: Cursor = con.execute(
    '''INSERT INTO bet
       (participant1_id, participant2_id, description, state, created_by_discord_id)
       VALUES (?, ?, ?, 'active', ?)''',
    (creator.id, opponent.id, description, str(ctx.author.id))
  )
  con.commit()

  if cur.lastrowid is None:
    raise SqlError('Ticket creation did not return ticket ID')
  ticket_num: int = cur.lastrowid

  await ctx.channel.send(f'alrighty your ticket is {format_ticket_id(ticket_num)} good luck champ')


@bot.command(
  help="bet's all done? well then, better let me know who won! show me ur ticket and ur winner, and i'll put it up on that thar leadrbord")
@ignore_bots
@is_registered(con)
async def resolve(ctx: Context, display_bet_id: int, winner_name: str, *, notes: str = ''):
  # Note: We ignore the winner_name value and just fetch it straight from the mentions.

  resolver = user.from_discord_user(ctx.author, con)

  try:
    try:
      bet_id = parse_ticket_id(display_bet_id)
    except ValueError as e:
      raise BungoError("that don't look like a proper ticket numbr") from e

    bet = con.execute('SELECT participant1_id, participant2_id, description, state FROM bet WHERE id = ?',
                      (bet_id,)).fetchone()

    if not bet:
      raise BungoError("i ain't know nothin bout that ticket numbr")

    participant1_id, participant2_id, description, state = bet

    if state != 'active':
      raise BungoError("cmon champ, that wager's long gone by now")

    if resolver.id not in (participant1_id, participant2_id):
      raise BungoError("slow down pardner, you ain't a part of that there wager")

    if not ctx.message.mentions:
      raise BungoError('u gotta @mention the winner!')

    participants = user.find_ids([participant1_id, participant2_id], con)

    participant1 = participants[participant1_id]
    participant2 = participants[participant2_id]
    mentioned_user = user.from_discord_user(ctx.message.mentions[0], con)

    if mentioned_user.id not in (participant1.id, participant2.id):
      raise BungoError(f'they aint a pard of this, its between {participant1.display_name} and {participant2.display_name}')

    if len(notes) > 280:
      raise BungoError('keep them notes under 280 characters pardner')
  except BungoError as e:
    print(f'Encountered Bungo error, returning message: {str(e)}')
    await ctx.channel.send(str(e))
    return
  except UnknownEntityError as e:
    print(f'Could not find entity: {str(e)}')
    await ctx.channel.send(f"i don know who {str(e)} is! have they said $howdy to ol' bungo?")
    return

  winner, loser = find_winner(mentioned_user, participant1, participant2)

  view = ResolutionConfirmView(
    con=con,
    bet_id=bet_id,
    winner_id=winner.id,
    winner_name=winner.display_name,
    loser_name=loser.display_name,
    resolver_discord_id=str(ctx.author.id),
    resolution_notes=None if not notes else notes
  )

  confirmation_msg = (
    f'wager: {description}\n'
    f'between: {winner.display_name} and {loser.display_name}\n\n'
    f'r ya sure {winner.display_name} wins?'
  )

  await ctx.channel.send(confirmation_msg, view=view)


@bot.command(help="bet not work out? just let me know the ticket number and i'll take it offa my books",
             aliases=['rules'])
@ignore_bots
@is_registered(con)
async def cancel(ctx, display_bet_id: int):
  canceller: User = user.from_discord_user(ctx.author, con)

  try:
    bet_id = parse_ticket_id(display_bet_id)
  except ValueError:
    await ctx.channel.send("that don't look like a proper ticket numbr")
    return

  bet = con.execute('SELECT * FROM bet WHERE id = ?', (bet_id,)).fetchone()

  if not bet:
    await ctx.channel.send("i ain't know nothin bout that ticket numbr")
    return

  if bet[5] != 'active':
    await ctx.channel.send("cmon champ, that wager's long gone by now")
    return

  participant1_id = bet[1]
  participant2_id = bet[2]

  if canceller.id not in (participant1_id, participant2_id):
    await ctx.channel.send("slow down pardner, you ain't a part of that there wager")
    return

  view = CancellationConfirmView(
    con=con,
    bet_id=bet_id,
    canceller_discord_id=str(ctx.author.id)
  )

  await ctx.channel.send('r ya sure?', view=view)


@bot.command(
  help="forgot ur ticket number eh? that's okay, i got 'em all up here, just ask and i'll give ya the full list of active bets")
@ignore_bots
@is_registered(con)
async def tickets(ctx: Context):
  caller: User = user.from_discord_user(ctx.author, con)

  query = '''
          SELECT b.id,
                 b.description,
                 u1.display_name as p1_name,
                 u2.display_name as p2_name,
                 b.created_at
          FROM bet b
                   JOIN user u1 ON b.participant1_id = u1.id
                   JOIN user u2 ON b.participant2_id = u2.id
          WHERE (b.participant1_id = ? OR b.participant2_id = ?)
            AND b.state = 'active'
          ORDER BY b.created_at DESC \
          '''

  tickets: list[Row] = con.execute(query, (caller.id, caller.id)).fetchall()

  if not tickets:
    await ctx.channel.send("u ain't got no active wagers right now pardner")
    return

  lines: list[str] = ['```', 'ur active tickets', '━━━━━━━━━━━━━━━━━━━━━━━']

  for ticket_id, description, p1_name, p2_name, created_at in tickets:
    display_ticket_id = format_ticket_id(ticket_id)
    lines.append(f'#{display_ticket_id}: {description}')
    lines.append(f'  between {p1_name} and {p2_name}')
    lines.append(f"  created: {created_at.strftime('%d-%m-%y')}")
    lines.append('')

  lines.append('━━━━━━━━━━━━━━━━━━━━━━━')
  lines.append('```')

  await ctx.channel.send('\n'.join(lines))


@bot.command(help='check ur holdings - bungo dollars, bungo bux, and spins')
@ignore_bots
@is_registered(con)
async def wallet(ctx: Context):
  caller: User = user.from_discord_user(ctx.author, con)

  lines = ['```', f"{caller.display_name}'s wallet", '━━━━━━━━━━━━━━━━━━━━━━━']

  if caller.bungo_dollars >= 0:
    dollars_str = f'${caller.bungo_dollars}'
  else:
    dollars_str = f'-${abs(caller.bungo_dollars)}'

  lines.append(f'bungo dollars: {dollars_str}')
  lines.append(f'bungo bux:     {caller.bungo_bux}')
  lines.append(f'spins:         {caller.spins}')
  lines.append('━━━━━━━━━━━━━━━━━━━━━━━')
  lines.append('```')

  await ctx.channel.send('\n'.join(lines))


@bot.command(aliases=['leaderboard'], help="i can tell ya who's the better better outta u 'n ur buds")
@ignore_bots
async def leadrbord(ctx):
  query = '''
          WITH user_stats AS (SELECT u.display_name,
                                     u.bungo_dollars                                      AS balance,
                                     SUM(CASE WHEN b.winner_id = u.id THEN 1 ELSE 0 END)  AS wins,
                                     SUM(CASE WHEN b.winner_id != u.id THEN 1 ELSE 0 END) AS losses
                              FROM user u
                                       LEFT JOIN bet b ON (b.participant1_id = u.id OR b.participant2_id = u.id)
                                  AND b.state = 'resolved'
                              GROUP BY u.id, u.display_name, u.bungo_dollars
                              HAVING COUNT(CASE WHEN b.state = 'resolved' THEN 1 END) > 0)
          SELECT display_name, balance, wins, losses
          FROM user_stats
          ORDER BY balance DESC, wins DESC LIMIT 10 \
          '''

  results = con.execute(query).fetchall()

  if not results:
    await ctx.channel.send("ain't nobody played yet pardner")
    return

  lines = ['```', "big bungo's leadrbord", '━━━━━━━━━━━━━━━━━━━━━━━']

  for idx, (name, balance, wins, losses) in enumerate(results, 1):
    display_name = name[:15] + '...' if len(name) > 15 else name

    if balance >= 0:
      balance_str = f'${balance}'
    else:
      balance_str = f'-${abs(balance)}'

    rank_str = f'#{idx}'.ljust(4)
    name_str = display_name.ljust(18)
    balance_str = balance_str.rjust(6)
    winloss_str = f'({wins}W/{losses}L)'

    lines.append(f'{rank_str}{name_str}{balance_str}  {winloss_str}')

  lines.append('━━━━━━━━━━━━━━━━━━━━━━━')
  lines.append('```')

  await ctx.channel.send('\n'.join(lines))


@bot.command(help='see who owes whom in a fancy graph')
@ignore_bots
@is_registered(con)
async def debts(ctx: Context):
  debt_edges = calculate_global_debts(con)

  if not debt_edges:
    await ctx.channel.send("ain't nobody got debts yet pardner")
    return

  image_path = generate_debt_graph_image(debt_edges)

  if image_path is None:
    await ctx.channel.send('somethin went wrong generatin the graph pardner')
    return

  try:
    await ctx.channel.send(file=discord.File(image_path))
  finally:
    import os
    if image_path and os.path.exists(image_path):
      os.unlink(image_path)


if __name__ == '__main__':
  bot_token = os.getenv('DISCORD_BOT_TOKEN')
  if bot_token is None:
    print('Discord API token not found')
    sys.exit(1)
  else:
    bot.run(bot_token)
