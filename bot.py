import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Initialize bot with a command prefix
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Ensure bot is ready
@bot.event
async def on_ready():
    print(f"Bot is ready! Logged in as {bot.user}")

# Create an async function to load extensions (cogs)
async def load_extensions():
    await bot.load_extension('fetch')  
    await bot.load_extension('music_copyright')   

# Run the bot
async def main():
    async with bot:
        await load_extensions()  # Load all extensions (cogs)
        await bot.start(DISCORD_TOKEN)

# Start the bot
import asyncio
asyncio.run(main())
