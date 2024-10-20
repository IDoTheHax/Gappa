import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
import asyncio
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Load environment variables
load_dotenv()

class CopyrightChecker(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents, help_command=None)
        
        # Updated YoutubeDL options for yt-dlp
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'extract_flat': 'in_playlist',
            'quiet': True,
            'no_warnings': True,
            'force_generic_extractor': False
        }
        
        # Set up Spotify client
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id, client_secret))
        
    async def setup_hook(self):
        await self.add_cog(MusicCommands(self))

class MusicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='check')
    async def check_copyright(self, ctx, *, query):
        """Check copyright status of a song by title or YouTube URL"""
        async with ctx.typing():  # Shows typing indicator while processing
            try:
                # If it's a YouTube URL
                if 'youtube.com' in query or 'youtu.be' in query:
                    info = await self.get_youtube_info(query)
                    if info:
                        embed = await self.create_youtube_embed(info)
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send("❌ Couldn't fetch video information. Please make sure the URL is valid.")
                
                # If it's a song title (Spotify search)
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
                
                # Analyze the licensing information
                license_info = info.get('license', 'Standard YouTube License')
                copyrighted = license_info != 'Creative Commons'  # Most YouTube videos are copyrighted

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
        note = "This Check is Performed by Checking the information of the Video`s License"
        embed = discord.Embed(
            title="YouTube Video Information",
            description=f"[Watch on YouTube]({info.get('url')})",
            color=discord.Color.red()
        )
        
        embed.add_field(name="Title", value=info['title'], inline=False)
        embed.add_field(name="Channel", value=info['channel'], inline=True)
        embed.add_field(name="License", value=info['license'], inline=True)
        embed.add_field(name="Status", value=copyright_status, inline=True)
        embed.add_field(name="Note", value=note, inline=True)
        
        if info['thumbnail']:
            embed.set_thumbnail(url=info['thumbnail'])
        
        return embed

# Start the bot
bot = CopyrightChecker()
bot.run(os.getenv("DISCORD_TOKEN"))
