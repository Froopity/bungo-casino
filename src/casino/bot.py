import os

import discord
from discord.ext import commands
import dotenv

dotenv.load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$', intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


@bot.command()
async def howdy(ctx, display_name):
    if ctx.author == bot.user:
        return

    await ctx.channel.send(f'why howdy stranger, i\'m gon call u {display_name}!')


bot.run(os.getenv('DISCORD_BOT_TOKEN'))
