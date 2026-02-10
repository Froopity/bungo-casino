from sqlite3 import Connection
import discord

from casino.typing import guards

class CancellationConfirmView(discord.ui.View):
  def __init__(self, con: Connection, bet_id: int, canceller_discord_id: str):
    super().__init__(timeout=60.0)
    self.bet_id = bet_id
    self.canceller_discord_id = canceller_discord_id
    self.con = con

  async def interaction_check(self, interaction: discord.Interaction) -> bool:
    if str(interaction.user.id) != self.canceller_discord_id:
      await interaction.response.send_message(
        'slow down pardner, only the person who done what called me can do that',
        ephemeral=True
      )
      return False
    return True

  @discord.ui.button(label='yes', style=discord.ButtonStyle.green)
  async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
    self._disable_buttons()

    cur = self.con.execute(
      '''UPDATE bet
         SET state = 'cancelled'
         WHERE id = ?
           AND state = 'active' ''',
      (self.bet_id,)
    )
    self.con.commit()

    if cur.rowcount == 0:
      bet = self.con.execute('SELECT state FROM bet WHERE id = ?', (self.bet_id,)).fetchone()
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
    self._disable_buttons()

    await interaction.response.edit_message(
      content='alright pardner, cancellation cancelled',
      view=self
    )

  def _disable_buttons(self):
    for item in self.children:
        if guards.is_button(item):
            item.disabled = True
