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


async def parse_winner_for_bet(ctx, winner_arg, participant1_id, participant2_id, cur):
  winner_id = None

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


def name_is_bungo(name: str, bot_id) -> bool:
  return (name == '@bungo'
          or name == '<@1450042419964809328>'
          or name in str(bot_id))
