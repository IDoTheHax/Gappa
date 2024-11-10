import discord
import yt_dlp
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

class YouTubeAudioBot(discord.Client):
    def __init__(self):
        # Set up intents to allow reading message content
        intents = discord.Intents.default()
        intents.message_content = True  # Allows reading message content for command detection
        super().__init__(intents=intents)

    async def on_ready(self):
        print(f'Logged in as {self.user}')

    async def on_message(self, message):
        # Ignore messages from the bot itself
        if message.author == self.user:
            return

        # Check for the command prefix "!extract" and a YouTube link in the message
        if message.content.startswith("!extract"):
            try:
                # Extract the YouTube URL from the message
                url = message.content.split(" ")[1]
                if "youtube.com" not in url and "youtu.be" not in url:
                    await message.channel.send("Please provide a valid YouTube link after the command.")
                    return

                await message.channel.send("Downloading audio...")

                # Define a fixed filename to avoid special characters
                output_filename = "downloaded_audio.mp3"
                
                # Download audio using yt-dlp with a specified output template
                ydl_opts = {
                    'format': 'bestaudio',
                    'outtmpl': 'downloaded_audio.%(ext)s',  # Ensure filename consistency
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192'
                    }]
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(url, download=True)

                # Send the extracted audio file
                await message.channel.send("Audio extracted successfully!", file=discord.File(output_filename))

                # Cleanup the audio file after sending
                os.remove(output_filename)
                
            except IndexError:
                await message.channel.send("Please include a YouTube link after the command, like this: `!extract <YouTube URL>`")
            except Exception as e:
                await message.channel.send("An error occurred while extracting audio.")
                print(f"Error: {e}")

# Instantiate and run the bot
bot = YouTubeAudioBot()
bot.run(DISCORD_TOKEN)
