from dataclasses import dataclass
from sqlite3 import Cursor
from discord.abc import User

from discord.ext.commands.bot import Bot
from exceptions import BotNotAuthenticatedError, BungoError, UnknownEntityError

def is_valid_name(text):
  allowed = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%')
  return all(char in allowed for char in text)


def format_ticket_id(db_id: int) -> int:
  """Convert database ID to display ticket number.
  Examples: 5 -> 105, 15 -> 115, 123 -> 1123"""
  return int(f'1{db_id:02d}')


def parse_ticket_id(display_id: int) -> int:
  """Convert display ticket number back to database ID.
  Examples: 105 -> 5, 115 -> 15, 1123 -> 123"""
  id_str = str(display_id)
  if not id_str.startswith('1') or len(id_str) < 3:
    raise ValueError(f'Invalid ticket number format: {display_id}')
  return int(id_str[1:])


def get_user_id(user: User, cur: Cursor) -> str:
  discord_id = str(user.id)

  user_id = cur.execute(
    'SELECT id FROM user WHERE discord_id = ?',
    (discord_id,)
  ).fetchone()

  if not user_id:
    raise UnknownEntityError(user.name)

  return user_id


@dataclass(frozen=True)
class BetOutcome:
  winner_id: str
  winner_name: str
  loser_id: str
  loser_name: str


async def parse_winner_for_bet(elected_winner_id: str, participant1_id, participant2_id, cur):
  """
  Determine winner and loser and return their bungo names.
  """
  results = cur.execute(
      'SELECT id, display_name FROM user WHERE id IN (?, ?)',
      (participant1_id, participant2_id)
  ).fetchall()

  user_map = dict(results)

  try:
    name1 = user_map[participant1_id]
    name2 = user_map[participant2_id]
  except KeyError as e:
    raise UnknownEntityError(str(e)) from e

  if elected_winner_id not in (participant1_id, participant2_id):
    raise BungoError(f'they aint a pard of this, its between {name1} and {name2}')

  if participant1_id == elected_winner_id:
    return BetOutcome(
      winner_id=participant1_id,
      winner_name=name1,
      loser_id=participant2_id,
      loser_name=name2
    )

  return BetOutcome(
    winner_id=participant2_id,
    winner_name=name2,
    loser_id=participant1_id,
    loser_name=name1
  )


def name_is_bungo(name: str, bot_id) -> bool:
  return (name == '@bungo'
          or name == '<@1450042419964809328>'
          or name in str(bot_id))


def get_bot_id(bot: Bot) -> int:
    if bot.user is None:
        raise BotNotAuthenticatedError("bungo ain't logged in")
    return bot.user.id


def calculate_global_debts(cur):
  query = '''
    SELECT
      debtor.display_name,
      creditor.display_name,
      COUNT(*) as amount
    FROM bet b
    JOIN user debtor ON (
      CASE WHEN b.winner_id = b.participant1_id
           THEN b.participant2_id
           ELSE b.participant1_id END = debtor.id
    )
    JOIN user creditor ON b.winner_id = creditor.id
    WHERE b.state = 'resolved'
    GROUP BY debtor.id, creditor.id
  '''

  results = cur.execute(query).fetchall()
  return [(debtor, creditor, amount) for debtor, creditor, amount in results]


def calculate_net_debts(debt_edges):
  debt_map = {}

  for debtor, creditor, amount in debt_edges:
    pair = tuple(sorted([debtor, creditor]))
    if pair not in debt_map:
      debt_map[pair] = {}
    debt_map[pair][debtor] = debt_map[pair].get(debtor, 0) + amount

  net_debts = []
  for (user1, user2), debts in debt_map.items():
    user1_owes = debts.get(user1, 0)
    user2_owes = debts.get(user2, 0)

    net = user1_owes - user2_owes
    if net > 0:
      net_debts.append((user1, user2, net))
    elif net < 0:
      net_debts.append((user2, user1, -net))

  return net_debts


def generate_debt_graph_image(debt_edges):
  import base64
  import tempfile
  import urllib.parse
  import urllib.request

  net_debts = calculate_net_debts(debt_edges)

  theme_config = {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#D2B48C',
      'primaryTextColor': '#3E2723',
      'primaryBorderColor': '#8B4513',
      'lineColor': '#A0522D',
      'edgeLabelBackground': '#F5DEB3',
      'fontFamily': '"Courier New", monospace',
      'fontSize': '14px'
    }
  }

  frontmatter = '---\nconfig:\n'
  for key, val in theme_config.items():
    if key == 'themeVariables':
      frontmatter += '  themeVariables:\n'
      for var_key, var_val in val.items():
        frontmatter += f"    {var_key}: '{var_val}'\n"
    else:
      frontmatter += f'  {key}: {val}\n'
  frontmatter += '---'

  mermaid_lines = [frontmatter, 'graph LR']

  node_map = {}
  node_counter = 0

  for debtor, creditor, amount in net_debts:
    if debtor not in node_map:
      node_map[debtor] = f'N{node_counter}'
      node_counter += 1
    if creditor not in node_map:
      node_map[creditor] = f'N{node_counter}'
      node_counter += 1

    debtor_node = node_map[debtor]
    creditor_node = node_map[creditor]
    mermaid_lines.append(f'  {debtor_node}["{debtor}"] -->|${amount}| {creditor_node}["{creditor}"]')

  mermaid_code = '\n'.join(mermaid_lines)
  encoded = base64.urlsafe_b64encode(mermaid_code.encode('utf-8')).decode('utf-8')
  url = f'https://mermaid.ink/img/{encoded}?bgColor=faf0d2'

  try:
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
      urllib.request.urlretrieve(url, tmp.name)
      return tmp.name
  except Exception:
    return None
