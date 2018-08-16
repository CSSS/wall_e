import os
import sys
import time
import traceback
import asyncio
import json
import redis
import parsedatetime
import discord
import requests as req
import urllib
import re
from discord.ext import commands
from time import mktime
from embed import *

TOKEN = os.environ['TOKEN']

bot = commands.Bot(command_prefix='.')

r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
message_subscriber = r.pubsub(ignore_subscribe_messages=True)
message_subscriber.subscribe('__keyevent@0__:expired')

#TODO: add bot as author to all commands and maybe get rid of the titles
#      doesnt fit for some of them. just be sure to make it consistent

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.command()
async def ping(ctx):
    eObj = embed(description='Pong!', author=BOT_NAME, avatar=BOT_AVATAR)
    await ctx.send(embed=eObj)

@bot.command()
async def echo(ctx, arg):
    user = ctx.author.nick or ctx.author.name
    avatar = ctx.author.avatar_url
    str = [
        ['Says: ', arg]
        ]
    
    test = '**Says**: ' + arg
    eObj = embed(author=user, avatar=avatar, description=arg)
    
    await ctx.send(embed=eObj)

@bot.command()
async def newrole(ctx, roleToAdd):
    roleToAdd = roleToAdd.lower()
    guild = ctx.guild
    for role in guild.roles:
        if role.name == roleToAdd:
            eObj = embed(author=BOT_NAME, avatar=BOT_AVATAR, description="Role \"" + roleToAdd + "\" exists. Calling **`.iam " + roleToAdd +"`** will add you to it.")
            await ctx.send(embed=eObj)
            return
    role = await guild.create_role(name=roleToAdd)

    #config the role and add to the user
    await role.edit(mentionable=True)
    await ctx.author.add_roles(role)

    eObj = embed(author=BOT_NAME, avatar=BOT_AVATAR, description="You have successfully created role **`" + roleToAdd + "`**.\nThe role has been given to you.")
    await ctx.send(embed=eObj)

@bot.command()
async def deleterole(ctx, roleToDelete):
    roleToDelete = roleToDelete.lower()
    role = discord.utils.get(ctx.guild.roles, name=roleToDelete)
    if role == None:
        eObj = embed(author=BOT_NAME, avatar=BOT_AVATAR, description="Role **`" + roleToDelete + "`** does not exist.")
        await ctx.send(embed=eObj)
        return
    role = discord.utils.get(ctx.guild.roles, name=roleToDelete)
    membersOfRole = role.members
    if not membersOfRole:
        deleteRole = await role.delete()
        eObj = embed(author=BOT_NAME, avatar=BOT_AVATAR, description="Role **`" + roleToDelete + "`** deleted.")
        await ctx.send(embed=eObj)
    else:
        eObj = embed(author=BOT_NAME, avatar=BOT_AVATAR, description="Role **`" + roleToDelete + "`** has members. Cannot delete.")
        await ctx.send(embed=eObj)

@bot.command()
async def iam(ctx, roleToAdd):
    roleToAdd = roleToAdd.lower()
    role = discord.utils.get(ctx.guild.roles, name=roleToAdd)
    if role == None:
        eObj = embed(author=BOT_NAME, avatar=BOT_AVATAR, description="Role **`" + roleToAdd + "**` doesn't exist.\nCalling .newrole " + roleToAdd)
        await ctx.send(embed=eObj)
        return
    user = ctx.message.author
    await user.add_roles(role)
    eObj = embed(author=BOT_NAME, avatar=BOT_AVATAR, description="You have successfully been added to role **`" + roleToAdd + "`**.")
    await ctx.send(embed=eObj)
    
@bot.command()
async def iamn(ctx, roleToRemove):
    roleToRemove = roleToRemove.lower()
    role = discord.utils.get(ctx.guild.roles, name=roleToRemove)
    if role == None:
        eObj = embed(author=BOT_NAME, avatar=BOT_AVATAR, description="Role **`" + roleToRemove + "`** doesn't exist.")
        await ctx.send(embed=eObj)
        return
    user = ctx.message.author
    await user.remove_roles(role)
    eObj = embed(author=BOT_NAME, avatar=BOT_AVATAR, description="You have successfully been remove from role **`" + roleToRemove + "`**.")
    await ctx.send(embed=eObj)

@bot.command()
async def whois(ctx, roleToCheck):
    memberString = ""
    role = discord.utils.get(ctx.guild.roles, name=roleToCheck)
    if role == None:
        eObj = embed(author=BOT_NAME, avatar=BOT_AVATAR, description="**`" + roleToCheck + "`** does not exist.")
        await ctx.send(embed=eObj)
        return
    membersOfRole = role.members
    if not membersOfRole:
        eObj = embed(author=BOT_NAME, avatar=BOT_AVATAR, description="No members in role **`" + roleToCheck + "`**.")
        await ctx.send(embed=eObj)
        return
    for members in membersOfRole:
        name = members.nick or members.name
        memberString += name + "\n"
    eObj = embed(author=BOT_NAME, avatar=BOT_AVATAR, description="Members belonging to role **`" + roleToCheck + "`**:\n" + memberString)

    await ctx.send(embed=eObj)

@bot.command()
async def poll(ctx, *questions):
    if len(questions) > 12:
        eObj = embed(title='Poll Error', author=BOT_NAME, avatar=BOT_AVATAR, description='Please only submit a maximum of 11 options for a multi-option question.')
        await ctx.send(embed=eObj)
        return
    elif len(questions) == 1:
        eObj = embed(title='Poll', description=questions[0])
        post = await ctx.send(embed=eObj)
        await post.add_reaction(u"\U0001F44D")
        await post.add_reaction(u"\U0001F44E")
        return
    if len(questions) == 2:
        eObj = embed(title='Poll Error', author=BOT_NAME, avatar=BOT_AVATAR, description='Please submit at least 2 options for a multi-option question.')
        await ctx.send(embed=eObj)
        return
    elif len(questions) == 0:
        eObj = embed(title='Usage', author=BOT_NAME, avatar=BOT_AVATAR, description='.poll <Question> [Option A] [Option B] ...')
        await ctx.send(embed=embed)
        return
    else:
        questions = list(questions)
        optionString = "\n"
        numbersEmoji = [":zero:", ":one:", ":two:", ":three:", ":four:", ":five:", ":six:", ":seven:", ":eight:", ":nine:", ":keycap_ten:"]
        numbersUnicode = [u"0\u20e3", u"1\u20e3", u"2\u20e3", u"3\u20e3", u"4\u20e3", u"5\u20e3", u"6\u20e3", u"7\u20e3", u"8\u20e3", u"9\u20e3", u"\U0001F51F"]
        question = questions.pop(0)
        options = 0
        for m, n in zip(numbersEmoji, questions):
            optionString += m + ": " + n +"\n"
            options += 1
        
        content = [['Options:', optionString]]
        eObj = embed(title='Poll:', author=BOT_NAME, avatar=BOT_AVATAR, description=question, content=content)
        pollPost = await ctx.send(embed=eObj)

        for i in range(0, options):
            await pollPost.add_reaction(numbersUnicode[i])

@bot.command()
async def remindme(ctx, timeUntil, message):
    time_struct, parse_status = parsedatetime.Calendar().parse(timeUntil)
    if parse_status == 0:
        eObj = embed(author=BOT_NAME, avatar=BOT_AVATAR, description='Could not parse time!')
        await ctx.send(embed=eObj)
        return
    expire_seconds = int(mktime(time_struct) - time.time())
    json_string = json.dumps({'cid': ctx.channel.id, 'mid': ctx.message.id})
    r.set(json_string, '', expire_seconds)
    fmt = 'Reminder set for {0} seconds from now'

    eObj = embed(author=BOT_NAME, avatar=BOT_AVATAR, description=fmt.format(expire_seconds))
    await ctx.send(embed=eObj)

@bot.command()
async def listroles(ctx):
    guild = ctx.guild
    output=""
    for role in guild.roles:
        if (role.name != "@everyone"):
            output+="\t\""+role.name+"\"\n"
    
    eObj = embed(title="Roles Available", description=output)
    
    await ctx.message.delete()
    await ctx.author.send(embed=eObj)

async def get_messages():
    await bot.wait_until_ready()
    while True:
        message = message_subscriber.get_message()
        if message is not None and message['type'] == 'message':
            try:
                cid_mid_dct = json.loads(message['data'])
                chan = bot.get_channel(cid_mid_dct['cid'])
                msg = await chan.get_message(cid_mid_dct['mid'])
                ctx = await bot.get_context(msg)
                if ctx.valid:
                    fmt = '<@{0}> ```{1}```'
                    await ctx.send(fmt.format(ctx.message.author.id, ctx.message.content))
            except Exception as error:
                print('Ignoring exception when generating reminder:', file=sys.stderr)
                traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        await asyncio.sleep(2)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        fmt = '```Missing argument: {0}```'
        await ctx.send(fmt.format(error.param))
    else:
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

@bot.event
async def on_ready():
    bot.loop.create_task(get_messages())
    
    global BOT_NAME 
    BOT_NAME = bot.user.name
    
    global BOT_AVATAR
    BOT_AVATAR = bot.user.avatar_url

    print("ZA WARUDOOO!!!!")

@bot.command()
async def urban(ctx, *arg):
    queryString = ''
    for x in arg:
        queryString += x

    url = 'http://api.urbandictionary.com/v0/define?term=%s' % queryString
    urbanUrl = 'https://www.urbandictionary.com/define.php?term=%s' % queryString

    res = req.get(url)
    
    if(res.status_code != 404):
        data = res.json()
    else:
        data = ''

    data = data['list']
    if not data:
        eObj = embed(title="Urban Results", author=BOT_NAME, avatar=BOT_AVATAR, colour=0xfd6a02, description=":thonk:404:thonk:You searched something dumb didn't you?")
        await ctx.send(embed=eObj)
        return
    else:
        content = [
            ['Definition', data[1]['definition']], 
            ['Link', urbanUrl]
            ]
        eObj = embed(title='Results from Urban Dictionary', author=BOT_NAME, avatar=BOT_AVATAR, colour=0xfd6a02, content=content)
        await ctx.send(embed=eObj)
    print(data[0])

@bot.command()
async def sfu(ctx, *course):
    year = time.localtime()[0]
    term = time.localtime()[1]

    if(term <= 4):
        term = 'spring'
    elif(term >= 5 and term <= 8):
        term = 'summer'
    else:
        term = 'fall'

    #need to check if we need to manually split the arg
    if(len(course) == 1):
        #split
        str = re.findall('(\d*\D+)', course[0])
        if(len(str) < 2):
            str = re.split('(\d+)', course[0])

        
        courseCode = str[0]
        courseNum = str[1]

    else:
        courseCode = course[0]
        courseNum = course[1]
    
    sfuUrl='http://www.sfu.ca/students/calendar/%s/%s/courses/%s/%s.html' % (year, term, courseCode, courseNum)
    #grab the things
    url = 'http://www.sfu.ca/bin/wcm/academic-calendar?%s/%s/courses/%s/%s' % (year, term, courseCode, courseNum)
    
    res = req.get(url)
    if(res.status_code != 404):
        data = res.json()
    else:
        data = '404'

    
    title='Results from SFU'
    colour=0xA6192E
    link='[here](%s)' % sfuUrl
    #thumbnail <do later>
    footer='Written by VJ'

    fields = [
        [data['title'], data['description']], 
        ["URL", link]
    ]

    
    embedObj = embed(title=title, author=BOT_NAME, avatar=BOT_AVATAR, content=fields, colour=colour, footer=footer)
    
    await ctx.send(embed=embedObj)
    

bot.run(TOKEN)
