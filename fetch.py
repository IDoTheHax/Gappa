import discord
from discord.ext import commands
from googleapiclient.discovery import build
import os

# YouTube API client setup
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

class FetchCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Fetch command
    @commands.command(name="fetch")
    async def fetch_video_info(self, ctx, yt_link):
        try:
            video_info = self.get_video_info(yt_link)
            video_details = (f"**Title:** {video_info['title']}\n"
                             f"**Description:** {video_info['description']}\n"
                             f"**Channel:** {video_info['channel_title']}\n"
                             f"**Published on:** {video_info['publish_date']}\n"
                             f"**Views:** {video_info['views']}\n"
                             f"**Likes:** {video_info['likes']}\n"
                             f"**Comments:** {video_info['comments']}\n"
                             f"**Duration:** {video_info['duration']}\n\n"
                             f"**Channel Subscribers:** {video_info['channel_subscribers']}\n"
                             f"**Total Videos:** {video_info['channel_videos']}")
            await ctx.send(video_details)
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    def get_video_info(self, video_url):
        video_id = video_url.split('v=')[-1]  # Extract video ID from URL

        # Fetch video details from YouTube API
        video_request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=video_id
        )
        video_response = video_request.execute()

        if not video_response['items']:
            raise Exception("Invalid YouTube video link or video not found.")

        video_data = video_response["items"][0]
        channel_id = video_data["snippet"]["channelId"]

        # Fetch channel details
        channel_request = youtube.channels().list(
            part="snippet,statistics",
            id=channel_id
        )
        channel_response = channel_request.execute()
        channel_data = channel_response["items"][0]

        return {
            "title": video_data["snippet"]["title"],
            "description": video_data["snippet"]["description"],
            "channel_title": video_data["snippet"]["channelTitle"],
            "publish_date": video_data["snippet"]["publishedAt"],
            "views": video_data["statistics"].get("viewCount", "N/A"),
            "likes": video_data["statistics"].get("likeCount", "N/A"),
            "comments": video_data["statistics"].get("commentCount", "N/A"),
            "duration": video_data["contentDetails"]["duration"],
            "channel_subscribers": channel_data["statistics"].get("subscriberCount", "N/A"),
            "channel_videos": channel_data["statistics"]["videoCount"]
        }

