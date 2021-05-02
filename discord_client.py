import os

import discord
from dotenv import load_dotenv

import studiegidsbot as sgbot

client = discord.Client()

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

sgbot.init()


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')


@client.event
async def on_message(msg):
    if msg.author == client.user:
        return

    resp = sgbot.chatbot_response(msg.content)
    await msg.channel.send(resp)


client.run(TOKEN)
