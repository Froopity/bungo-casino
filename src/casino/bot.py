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


if __name__ == '__main__':
    bot.run(os.getenv('DISCORD_BOT_TOKEN'))
