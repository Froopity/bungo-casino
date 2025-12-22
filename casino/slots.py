import random


def generate_slot_grid():
  """Generate a 3x5 grid of symbols ($ or O) with 50% chance of $."""
  grid = []
  for _ in range(3):
    row = []
    for _ in range(5):
      # 50% chance of $, 50% chance of O
      symbol = '$' if random.random() < 0.5 else 'O'
      row.append(symbol)
    grid.append(row)
  return grid


def calculate_payout(middle_row):
  """
  Calculate payout based on consecutive $ signs in the middle row.
  Payouts:
  - 3 consecutive $ = 1
  - 4 consecutive $ = 2
  - 5 consecutive $ = 6

  Returns tuple of (payout_amount, consecutive_count)
  """
  max_consecutive = 0
  current_consecutive = 0

  for symbol in middle_row:
    if symbol == '$':
      current_consecutive += 1
      max_consecutive = max(max_consecutive, current_consecutive)
    else:
      current_consecutive = 0

  # Payout table
  payout_table = {
    3: 1,
    4: 2,
    5: 6
  }

  payout = payout_table.get(max_consecutive, 0)
  return payout, max_consecutive


def format_slot_frame(grid, payout):
  """
  Format the slot grid into an ASCII frame.

  Grid is expected to be a 3x5 list of symbols.
  Payout determines the header decoration.
  """
  top =                 '╔═════════════╗'
  header =              '║    BUNGO    ║ ◉'
  divider1 =            '╠═════════════╣ ║'
  top_row_template =    '║  {} {} {} {} {}  ║ ║'
  middle_row_template = '╠═ {} {} {} {} {} ═╬═╝'
  bottom_row_template = '║  {} {} {} {} {}  ║'
  bottom =              '╚═╦═════════╦═╝'
  tray =                '  ╚═════════╝  '

  # Generate header based on payout
  if payout == 0:
    header = '║    BUNGO    ║ ◉'
  elif payout == 1:
    header = '║ $  BUNGO  $ ║ ◉'
  elif payout == 2:
    header = '║ $$ BUNGO $$ ║ ◉'
  elif payout == 6:
    header = '║ $$ $$$$$ $$ ║ ◉'
  elif payout == 12:
    header = '║ $$$$$$$$$$$ ║ ◉'
  else:
    # Fallback to default header from above
    pass

  # Format the three rows
  row1 = top_row_template.format(*grid[0])
  row2 = middle_row_template.format(*grid[1])
  row3 = bottom_row_template.format(*grid[2])

  frame = '\n'.join([
    top,
    header,
    divider1,
    row1,
    row2,
    row3,
    bottom,
    tray
  ])

  return frame


def spin_slots():
  """
  Execute a complete slot spin and return the formatted frame and payout.

  Returns tuple of (frame_string, payout_amount, consecutive_count)
  """
  # 1/100 chance of mega jackpot
  if random.randint(1, 100) == 1:
    # Mega jackpot!
    grid = [
      ['X', 'X', 'X', 'X', 'X'],
      ['B', 'U', 'N', 'G', 'O'],
      ['X', 'X', 'X', 'X', 'X']
    ]
    payout = 12
    frame = format_slot_frame(grid, payout)
    return frame, payout

  # Normal spin
  grid = generate_slot_grid()
  middle_row = grid[1]
  payout, consecutive = calculate_payout(middle_row)
  frame = format_slot_frame(grid, payout)

  return frame, payout


if __name__ == '__main__':
  # Test the slot machine
  print("Testing Bungo's Slot Machine\n")

  for i in range(5):
    frame, payout = spin_slots()
    print(frame)
    if payout > 0:
      print(f'\nWinner! Payout: {payout}')
    else:
      print('\nNo win')
    print('\n' + '='*20 + '\n')
