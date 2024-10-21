import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
import asyncio
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from googleapiclient.discovery import build

# Load environment variables
load_dotenv()

# YouTube API client setup
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

class CopyrightChecker(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents, help_command=None)

        self.ydl_opts = {
            'format': 'bestaudio/best',
            'extract_flat': 'in_playlist',
            'quiet': True,
            'no_warnings': True,
            'force_generic_extractor': False
        }
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id, client_secret))
        
    async def setup_hook(self):
        await self.add_cog(MusicCommands(self))

    async def on_ready(self):
        print(f"Bot is ready! Logged in as {self.user}")
        await self.change_presence(activity=discord.Game(name="With Copyright! Want to know more? Type !help"))

class MusicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='check')
    async def check_copyright(self, ctx, *, query):
        """Check copyright status of a song by title or YouTube URL"""
        async with ctx.typing():
            try:
                # If it's a YouTube URL
                if 'youtube.com' in query or 'youtu.be' in query:
                    info = await self.get_youtube_info(query)
                    if info:
                        embed = await self.create_youtube_embed(info)
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send("❌ Couldn't fetch video information. Please make sure the URL is valid.")
                
                else:
                    results = await self.search_spotify_info(query)
                    if results:
                        embed = await self.create_spotify_embed(results)
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send("❌ No information found for this song on Spotify.")
   
            except Exception as e:
                error_msg = f"❌ An error occurred: {str(e)}"
                if "HTTP Error 429" in str(e):
                    error_msg = "❌ Rate limit reached. Please try again later."
                elif "This video is unavailable" in str(e):
                    error_msg = "❌ This video is unavailable or private."
                await ctx.send(error_msg)

    async def get_youtube_info(self, url):
        """Get copyright information from YouTube video"""
        with YoutubeDL(self.bot.ydl_opts) as ydl:
            try:
                info = await asyncio.to_thread(ydl.extract_info, url, download=False)
                if not info:
                    return None
                
                license_info = info.get('license', 'Standard YouTube License')
                title = info.get('title', '').lower()
                description = info.get('description', '').lower()

                # Improved copyright detection logic
                is_creative_commons = (
                    'creative commons' in description or
                    license_info.lower() == 'creative commons'
                )
                
                # Check for phrases indicating that the content might be free to use
                no_copyright_terms = ['no copyright', 'free to use', 'royalty-free', 'copyright free', 'public domain']
                contains_no_copyright = any(term in title or term in description for term in no_copyright_terms)
                
                # Consider the content non-copyrighted if it falls into these categories
                copyrighted = not (is_creative_commons or contains_no_copyright)

                return {
                    'title': info.get('title', 'Unknown'),
                    'channel': info.get('uploader', 'Unknown'),
                    'license': license_info,
                    'is_copyrighted': copyrighted,
                    'description': info.get('description', 'No description available'),
                    'thumbnail': info.get('thumbnail', None),
                    'duration': info.get('duration', 0),
                    'view_count': info.get('view_count', 0),
                    'upload_date': info.get('upload_date', 'Unknown'),
                    'url': info.get('webpage_url', url)
                }
            except Exception as e:
                print(f"Error extracting video info: {str(e)}")
                return None

    async def search_spotify_info(self, query):
        """Search for song information using Spotify"""
        try:
            results = self.bot.spotify.search(q=query, type='track', limit=1)
            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                # Assume that if a track is on Spotify, it's likely under copyright
                copyrighted = True
                return {
                    'title': track['name'],
                    'artist': ", ".join(artist['name'] for artist in track['artists']),
                    'album': track['album']['name'],
                    'release_date': track['album']['release_date'],
                    'spotify_url': track['external_urls']['spotify'],
                    'thumbnail': track['album']['images'][0]['url'] if track['album']['images'] else None,
                    'is_copyrighted': copyrighted
                }
            return None
        except Exception as e:
            print(f"Error fetching song info from Spotify: {str(e)}")
            return None

    async def create_spotify_embed(self, info):
        """Create Discord embed for Spotify track info"""
        copyright_status = "🔒 Copyrighted" if info['is_copyrighted'] else "✔️ Public Domain / Creative Commons"
        embed = discord.Embed(
            title="Spotify Track Information",
            description=f"[Listen on Spotify]({info['spotify_url']})",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Title", value=info['title'], inline=False)
        embed.add_field(name="Artist(s)", value=info['artist'], inline=True)
        embed.add_field(name="Album", value=info['album'], inline=True)
        embed.add_field(name="Release Date", value=info['release_date'], inline=True)
        embed.add_field(name="Status", value=copyright_status, inline=True)
        
        if info['thumbnail']:
            embed.set_thumbnail(url=info['thumbnail'])
        
        return embed

    async def create_youtube_embed(self, info):
        """Create Discord embed for YouTube video info"""
        copyright_status = "🔒 Copyrighted" if info['is_copyrighted'] else "✔️ Public Domain / Creative Commons"
        embed = discord.Embed(
            title="YouTube Video Information",
            description=f"[Watch on YouTube]({info.get('url')})",
            color=discord.Color.red()
        )
        
        embed.add_field(name="Title", value=info['title'], inline=False)
        embed.add_field(name="Channel", value=info['channel'], inline=True)
        embed.add_field(name="License", value=info['license'], inline=True)
        embed.add_field(name="Status", value=copyright_status, inline=True)
        embed.add_field(name="Note", value="This check is based on video license information, title, and description analysis.", inline=True)
        
        if info['thumbnail']:
            embed.set_thumbnail(url=info['thumbnail'])
        
        return embed

    @commands.command(name="fetch")
    async def fetch_video_info(self, ctx, yt_link):
        try:
            video_info = self.get_video_info(yt_link)
            embed = discord.Embed(
                title=video_info['title'],
                description=video_info['description'][:200] + "..." if len(video_info['description']) > 200 else video_info['description'],
                color=discord.Color.red(),
                url=yt_link
            )
            embed.set_author(name=video_info['channel_title'])
            embed.add_field(name="Published on", value=video_info['publish_date'], inline=True)
            embed.add_field(name="Views", value=f"{int(video_info['views']):,}", inline=True)
            embed.add_field(name="Likes", value=f"{int(video_info['likes']):,}", inline=True)
            embed.add_field(name="Comments", value=f"{int(video_info['comments']):,}", inline=True)
            embed.add_field(name="Duration", value=self.format_duration(video_info['duration']), inline=True)
            embed.add_field(name="Channel Subscribers", value=f"{int(video_info['channel_subscribers']):,}", inline=True)
            embed.add_field(name="Total Videos", value=f"{int(video_info['channel_videos']):,}", inline=True)
            
            if 'thumbnail' in video_info and video_info['thumbnail']:
                embed.set_thumbnail(url=video_info['thumbnail'])
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    def format_duration(self, duration):
        """Convert ISO 8601 duration to a more readable format"""
        duration = duration.replace('PT', '')
        hours = 0
        minutes = 0
        seconds = 0
        
        if 'H' in duration:
            hours, duration = duration.split('H')
            hours = int(hours)
        if 'M' in duration:
            minutes, duration = duration.split('M')
            minutes = int(minutes)
        if 'S' in duration:
            seconds = int(duration.replace('S', ''))
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"

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

        # Add this line to get the thumbnail URL
        thumbnail = video_data["snippet"]["thumbnails"]["high"]["url"] if "thumbnails" in video_data["snippet"] else None
        
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
            "channel_videos": channel_data["statistics"]["videoCount"],
            "thumbnail": thumbnail
        }

    @commands.command(name='help')
    async def help_command(self, ctx):
        embed = discord.Embed(
            title="Music Copyright Bot Help",
            description="Here are the available commands:",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="!check [song title or YouTube URL]",
            value="Check the copyright status of a song or YouTube video.",
            inline=False
        )
        embed.add_field(
            name="!fetch [YouTube URL]",
            value="Fetch detailed information about a YouTube video.",
            inline=False
        )
        embed.add_field(
            name="!help",
            value="Show this help message.",
            inline=False
        )
        await ctx.send(embed=embed)

# Start the bot
bot = CopyrightChecker()
bot.run(os.getenv("DISCORD_TOKEN"))
