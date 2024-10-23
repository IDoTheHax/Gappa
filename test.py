import discord
import os
import googleapiclient.discovery
from discord.ext import commands
from datetime import datetime

# Load environment variables (bot token, API key)
from dotenv import load_dotenv
load_dotenv()

# Create intents
intents = discord.Intents.default()
intents.message_content = True

# Discord bot setup
bot = commands.Bot(command_prefix="!", intents=intents)

# YouTube API setup
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
youtube_client = googleapiclient.discovery.build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# Function to get YouTube channel details
def get_channel_details(channel_id):
    request = youtube_client.channels().list(
        part="snippet,statistics,brandingSettings,contentDetails",
        id=channel_id
    )
    response = request.execute()

    if "items" in response and len(response["items"]) > 0:
        channel = response["items"][0]
        statistics = channel["statistics"]
        snippet = channel["snippet"]
        branding = channel["brandingSettings"]

        # Return parsed stats
        return {
            "title": snippet["title"],
            "description": snippet.get("description", "No description"),
            "subscribers": statistics.get("subscriberCount", "N/A"),
            "views": statistics.get("viewCount", "N/A"),
            "videos": statistics.get("videoCount", "N/A"),
            "watch_hours": round(int(statistics.get("viewCount", 0)) / 1000, 2),  # rough estimate
            "created_at": snippet["publishedAt"],
            "profile_pic": snippet["thumbnails"]["high"]["url"],
            "banner_url": branding["image"]["bannerExternalUrl"] if "image" in branding else None,
        }
    else:
        return None

# Function to get the latest video of a channel
def get_latest_video(channel_id):
    request = youtube_client.search().list(
        part="snippet",
        channelId=channel_id,
        order="date",
        maxResults=1
    )
    response = request.execute()

    if response["items"]:
        video = response["items"][0]
        return {
            "title": video["snippet"]["title"],
            "video_id": video["id"]["videoId"],
            "published_at": video["snippet"]["publishedAt"]
        }
    return None

# Function to get top viewed video of a channel
def get_top_video(channel_id):
    request = youtube_client.search().list(
        part="snippet",
        channelId=channel_id,
        order="viewCount",
        maxResults=1
    )
    response = request.execute()

    if response["items"]:
        video = response["items"][0]
        return {
            "title": video["snippet"]["title"],
            "video_id": video["id"]["videoId"]
        }
    return None

# Discord command to get detailed YouTube stats
@bot.command()
async def youtube(ctx, channel_id):
    stats = get_channel_details(channel_id)
    latest_video = get_latest_video(channel_id)
    top_video = get_top_video(channel_id)

    if stats:
        embed = discord.Embed(
            title=f"{stats['title']} - YouTube Channel Stats",
            description=stats['description'],
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=stats["profile_pic"])

        if stats["banner_url"]:
            embed.set_image(url=stats["banner_url"])

        # Add fields for stats
        embed.add_field(name="Subscribers", value=stats['subscribers'], inline=True)
        embed.add_field(name="Total Views", value=stats['views'], inline=True)
        embed.add_field(name="Total Videos", value=stats['videos'], inline=True)
        embed.add_field(name="Watch Hours (estimated)", value=stats['watch_hours'], inline=True)
        embed.add_field(name="Channel Created", value=stats['created_at'], inline=True)

        # Add latest video info
        if latest_video:
            embed.add_field(
                name="Latest Video",
                value=f"[{latest_video['title']}](https://www.youtube.com/watch?v={latest_video['video_id']})"
            )

        # Add top video info
        if top_video:
            embed.add_field(
                name="Top Video",
                value=f"[{top_video['title']}](https://www.youtube.com/watch?v={top_video['video_id']})"
            )

        await ctx.send(embed=embed)
    else:
        await ctx.send("Channel not found!")

# Start the bot
bot.run(os.getenv('DISCORD_TOKEN'))
