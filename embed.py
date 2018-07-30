import discord
import asyncio
import json

from discord.ext import commands

def embed(title, author, colour, url, thumbnail, content):
    temp = discord.Embed(title=title, type='rich')
    temp.add_field(name='name', value='pong!')
    return temp
    
def embed(title, img, c):
    temp = discord.Embed(title=title, type='rich')
    temp.add_field(name='first person', value='vj')
    temp.set_thumbnail(url=img)
    temp.colour = c
    
    #adding fields can be done via loops and json objs i guess? 
    
    return temp