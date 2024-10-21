import discord
from discord.ext import commands
import re

# Initialize the bot with a command prefix
bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

# Regular expression pattern to validate and extract video IDs
YOUTUBE_URL_PATTERN = r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})'

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

@bot.command()
async def thumb(ctx, url: str):
    # Extract the video ID using regex
    match = re.match(YOUTUBE_URL_PATTERN, url)
    if match:
        video_id = match.group(1)
        # Construct the HD thumbnail URL
        thumbnail_url = f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'

        # Create an embed to display the thumbnail
        embed = discord.Embed(
            title='YouTube Thumbnail',
            description='Here is the HD thumbnail of the provided video:',
            color=discord.Color.blue()
        )
        embed.set_image(url=thumbnail_url)
        embed.set_footer(text='Requested by ' + ctx.author.name)

        # Send the embed
        await ctx.send(embed=embed)
    else:
        await ctx.send('Please provide a valid YouTube link!')

# Replace 'YOUR_BOT_TOKEN' with the token from the Discord Developer Portal
bot.run('YOUR_BOT_TOKEN')
