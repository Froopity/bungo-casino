from sqlite3 import Connection
import discord

from casino.typing import guards

class ResolutionConfirmView(discord.ui.View):
  def __init__(self, con: Connection, bet_id: int, winner_id: str, winner_name: str, loser_name: str,
               resolver_discord_id: str, resolution_notes: str | None = None):
    super().__init__(timeout=60.0)
    self.con = con
    self.bet_id = bet_id
    self.winner_id = winner_id
    self.winner_name = winner_name
    self.loser_name = loser_name
    self.resolver_discord_id = resolver_discord_id
    self.resolution_notes = resolution_notes

  async def interaction_check(self, interaction: discord.Interaction) -> bool:
    if str(interaction.user.id) != self.resolver_discord_id:
      await interaction.response.send_message(
        'slow down pardner, only the person who done what called me can do that',
        ephemeral=True
      )
      return False
    return True

  @discord.ui.button(label='yes', style=discord.ButtonStyle.green)
  async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
    self._disable_buttons()

    # Get loser_id to update their bungo dollars
    bet = self.con.execute('SELECT participant1_id, participant2_id FROM bet WHERE id = ?', (self.bet_id,)).fetchone()
    loser_id = bet[0] if bet[1] == self.winner_id else bet[1]

    cur = self.con.cursor()

    cur.execute(
      '''UPDATE bet
         SET state                  = 'resolved',
             resolved_at            = CURRENT_TIMESTAMP,
             resolved_by_discord_id = ?,
             winner_id              = ?,
             resolution_notes       = ?
         WHERE id = ?
           AND state = 'active' ''',
      (self.resolver_discord_id, self.winner_id, self.resolution_notes, self.bet_id)
    )
    cur.execute('UPDATE user SET spins = spins + 1, bungo_dollars = bungo_dollars + 1 WHERE id = ?', (self.winner_id,))
    cur.execute('UPDATE user SET bungo_dollars = bungo_dollars - 1 WHERE id = ?', (loser_id,))
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
      content=f'congrertulatiorns {self.winner_name}, betrr luck next time {self.loser_name}',
      view=self
    )

  @discord.ui.button(label='nevrmind', style=discord.ButtonStyle.grey)
  async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
    self._disable_buttons()

    await interaction.response.edit_message(
      content='alright pardner, resolution cancelled',
      view=self
    )

  def _disable_buttons(self):
    for item in self.children:
        if guards.is_button(item):
            item.disabled = True
