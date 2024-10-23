import discord
from discord.ext import commands
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

# Initialize the YouTube API client
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
async def getid(ctx, handle: str):
    """Fetches the YouTube channel ID from a given handle"""
    try:
        # Remove '@' if the handle starts with it
        handle = handle.lstrip('@')
        
        # Search for the channel using the YouTube API
        request = youtube.channels().list(
            part="id",
            forUsername=handle
        )
        response = request.execute()

        if response["items"]:
            # Extract the channel ID
            channel_id = response["items"][0]["id"]
            await ctx.send(f"The channel ID for `{handle}` is `{channel_id}`.")
        else:
            await ctx.send(f"No channel found for the handle `{handle}`.")

    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

# Run the bot
bot.run(DISCORD_TOKEN)
