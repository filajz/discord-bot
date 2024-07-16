import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Initialize bot
bot = commands.Bot(command_prefix="/")

@bot.event
async def on_ready():
    logging.info(f'{bot.user} has connected to Discord!')

@bot.command()
async def ping(ctx):
    await ctx.send('pong')

# Run bot
bot.run(TOKEN)
