import discord,asyncio
import queue
from discord import app_commands
import googleapiclient.discovery 
from googleapiclient.discovery import build
import requests
import io
import base64
from PIL import Image, PngImagePlugin
import nacl 
import yt_dlp as youtube_dl
import ytdl
import os
import ffmpeg

os.environ['API_KEY'] = "AIzaSyAPlXWGgwJbY2SGeSaBUS-5TmqkGMLEAmg"
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey = os.environ["API_KEY"])


async def send_message(message, user_message, is_private):
    try:
        response = queue.handle_responses(user_message, message)
        await message.author.send(response) if is_private else await message.channel.send(response)
    except Exception as e:
        print(e)

def run_bot():
    TOKEN = 'MTA1NTk1NzM0Njk4NTE4OTUyOA.GZ2Frh.Mz9LfTVaD64_800gBrHUmdaA-kqf8tv7GbvVi8'
    intents = discord.Intents.default()
    intents.message_content = True

    client = discord.Client(intents=intents)
    tree = app_commands.CommandTree(client)

    @tree.command(name = "hello", description = "say hi") #Add the guild ids in which the slash command will appear. If it should be in all, remove the argument, but note that it will take some time (up to an hour) to register the command if it's for all guilds.
    async def hello(interaction, message: str):
        await interaction.response.send_message("Hello {}!".format(message))
    
    @tree.command(name = "help", description= "list of commands")
    async def help(interaction):
        cmds = " ``` tip for generation: add multiple prompts seperated by ',' for more accurate generation ```"
        await interaction.response.send_message(cmds)


    @tree.command(name = "join", description= "join a valid voice channel to connect bot")
    async def play(interaction):
        if interaction.user.voice is None:
            await interaction.response.send_message("You must be in a valid voice channel to use this command")
            return
        
        channel = interaction.user.voice.channel
        await channel.connect()
        await interaction.response.send_message("Joined!")

    @tree.command(name = "leave", description= "leave channel")
    async def leave(interaction):
        voice = interaction.guild.voice_client
        if voice is None:
            await interaction.response.send_message("Must be in voice channel to leave")
            return
        if voice.is_playing():
            voice.stop()
        await voice.disconnect()
        await interaction.response.send_message("Goodbye for now!")
    
    @tree.command(name="pause", description="pause music (use again to resume)")
    async def pause_music(interaction):
        voice_client = interaction.guild.voice_client
        if voice_client.is_playing():
            voice_client.pause()
            await interaction.response.send_message("**Paused** the music")
        else:
            if voice_client.is_paused():
                voice_client.resume()
                await interaction.response.send_message("**Resumed** the music")
            else:
                await interaction.response.send_message("The bot is not currently playing anything")
    
    @tree.command(name = "play", description= "play music in channel")
    async def music(interaction, message: str):

        await interaction.response.defer()

        voice_client = interaction.guild.voice_client
        #if voice_client.is_playing():
        #        await interaction.response.send_message("**Added to queue**")
        #        return
        if interaction.user.voice is None:
            await interaction.response.send_message("Must be in voice channel to play music")
            return
        elif interaction.user.voice and (voice_client is None):
            channel = interaction.user.voice.channel
            await channel.connect()
            voice_client = interaction.guild.voice_client
        #if len(queue) > 1 and voice_client.is_playing() == False:
        #    queue.remove(queue[0])

        if voice_client.is_playing():
            voice_client.source = discord.FFmpegPCMAudio(executable = "C:/Users/matth/pathff/ffmpeg.exe", source = 'tempsong.mp3')
        if os.path.exists('song.mp3'):
            os.remove('song.mp3')
        
        #if message != "CODE_SKIP":
        if ("https://www.youtube.com/watch?v=" or "youtu.be") not in message:
            request = youtube.search().list(
                part = 'id',
                q= message,
                type="video",
                videoDefinition = "high",
                maxResults = 1
            )

            response = request.execute()
            video_id = response['items'][0]['id']['videoId']
            print(video_id)

            url = "https://www.youtube.com/watch?v={}".format(video_id)
        else:
            url = message
    
        if '&' in url:
            url = url.split('&')[0]

            
        #else:
            
        
        filename = 'song.mp3'
        ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': filename
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)


        source = discord.FFmpegPCMAudio(executable = "C:/Users/matth/pathff/ffmpeg.exe", source = filename)
        if voice_client.is_playing():
            voice_client.source = source
        else:
            voice_client.play(source)
        
        await interaction.followup.send("**Now playing:** {}".format(url)) 
        

    #@tree.command(name = "skip", description= "skip song", guild= discord.Object(id=973686008245788703))
    #async def skip(interaction):

    #    queue.remove(queue[0])

    #    if len(queue) > 1:
    #        await music(interaction, "CODE_SKIP")
    #    else:
    #        await interaction.response.send_message("Nothing to skip to...")

    @tree.command(name = "generate", description = "enter prompt for ai generation")
    async def gen(interaction, message: str):
        await interaction.response.defer()
        await asyncio.sleep(1)
        data = {
                "prompt": message + ",masterpiece, best quality, ultra-detailed, 4k, best lighting, cinematic",
                "batch_size": 1,
                "n_iter": 1,
                "steps": 20,
                "cfg_scale": 7,
                "width": 512,
                "height": 512,
                "negative_prompt": "(worst quality, low quality:1.4),",
                "override_settings": {},
                "override_settings_restore_afterwards": True,
                "sampler_index": "Euler",
                }
        response_z = requests.post(url='http://127.0.0.1:7860/sdapi/v1/txt2img', json=data)
        r = response_z.json()
        
        if 'images' in r:
            for i in r['images']:
                image = Image.open(io.BytesIO(base64.b64decode(i.split(",",1)[0])))

        image.save('output.png')

        picture = discord.File('output.png')

        await interaction.followup.send(file=picture, content="Finished: **{}!**".format(message))        

    @client.event
    async def on_ready():
        await tree.sync()
        print("Ready!")

    client.run(TOKEN)
