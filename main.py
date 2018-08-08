import os
import sys
import time
import traceback
import asyncio
import json
import redis
import parsedatetime
import discord
import urllib
from discord.ext import commands
from time import mktime
import testenv

TOKEN = os.environ['TOKEN']

bot = commands.Bot(command_prefix='.')

r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
message_subscriber = r.pubsub(ignore_subscribe_messages=True)
message_subscriber.subscribe('__keyevent@0__:expired')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.command()
async def ping(ctx):
    await ctx.send('```pong!```')


@bot.command()
async def echo(ctx, arg):
    user = ctx.author.nick or ctx.author.name
    await ctx.send(user + " says: " + arg)
    
@bot.command()
async def newrole(ctx, roleToAdd):
    roleToAdd = roleToAdd.lower()
    guild = ctx.guild
    for role in guild.roles:
        if role.name == roleToAdd:
            await ctx.send("```" + "Role '" + roleToAdd + "' exists. Calling .iam " + roleToAdd +" will add you to it." + "```")
            return
    role = await guild.create_role(name=roleToAdd)
    await role.edit(mentionable=True)
    await ctx.send("```" + "You have successfully created role '" + roleToAdd + "'. Calling .iam " + roleToAdd + " will add you to it." + "```")

@bot.command()
async def deleterole(ctx, roleToDelete):
    roleToDelete = roleToDelete.lower()
    role = discord.utils.get(ctx.guild.roles, name=roleToDelete)
    if role == None:
        await ctx.send("```" + "Role '" + roleToDelete + "' does not exist." + "```")
        return
    role = discord.utils.get(ctx.guild.roles, name=roleToDelete)
    membersOfRole = role.members
    if not membersOfRole:
        deleteRole = await role.delete()
        await ctx.send("```" + "Role '" + roleToDelete + "' deleted." + "```")
    else:
        await ctx.send("```" + "Role '" + roleToDelete + "' has members. Cannot delete." + "```")

@bot.command()
async def iam(ctx, roleToAdd):
    roleToAdd = roleToAdd.lower()
    role = discord.utils.get(ctx.guild.roles, name=roleToAdd)
    if role == None:
        await ctx.send("```" + "Role '" + roleToAdd + "' does not exist. Calling .newrole " + roleToAdd +" will create it." + "```")
        return
    user = ctx.message.author
    await user.add_roles(role)
    await ctx.send("```" + "You have successfully been added to role '" + roleToAdd + "'." + "```")
    
@bot.command()
async def iamn(ctx, roleToRemove):
    roleToRemove = roleToRemove.lower()
    role = discord.utils.get(ctx.guild.roles, name=roleToRemove)
    if role == None:
        await ctx.send("```" + "Role '" + roleToRemove + "' does not exist." + "```")
        return
    user = ctx.message.author
    await user.remove_roles(role)
    await ctx.send("```" + "You have successfully been removed from role '" + roleToRemove + "'." + "```")

@bot.command()
async def whois(ctx, roleToCheck):
    memberString = ""
    role = discord.utils.get(ctx.guild.roles, name=roleToCheck)
    if role == None:
        await ctx.send("```" + "Role '" + roleToCheck + "' does not exist." + "```")
        return
    membersOfRole = role.members
    if not membersOfRole:
        await ctx.send("```" + "No members in role '" + roleToCheck + "'." + "```")
        return
    for members in membersOfRole:
        name = members.nick or members.name
        memberString += name + "\n"
    await ctx.send("Members belonging to role `" + roleToCheck + "`:\n" + "```" + memberString + "```")

@bot.command()
async def poll(ctx, *questions):
    if len(questions) > 12:
        await ctx.send("Poll Error:\n```Please only submit a maximum of 11 options for a multi-option question.```")
        return
    elif len(questions) == 1:
        post = await ctx.send("Poll:\n" + "```" + questions[0] + "```")
        await post.add_reaction(u"\U0001F44D")
        await post.add_reaction(u"\U0001F44E")
        return
    if len(questions) == 2:
        await ctx.send("Poll Error:\n```Please submit at least 2 options for a multi-option question.```")
        return
    elif len(questions) == 0:
        await ctx.send('```Usage: .poll <Question> [Option A] [Option B] ...```')
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
        pollPost = await ctx.send("Poll:\n```" + question + "```" + optionString)
        for i in range(0, options):
            await pollPost.add_reaction(numbersUnicode[i])

@bot.command()
async def remindme(ctx, timeUntil, message):
    time_struct, parse_status = parsedatetime.Calendar().parse(timeUntil)
    if parse_status == 0:
        await ctx.send('```Could not parse time!```')
        return
    expire_seconds = int(mktime(time_struct) - time.time())
    json_string = json.dumps({'cid': ctx.channel.id, 'mid': ctx.message.id})
    r.set(json_string, '', expire_seconds)
    fmt = '```Reminder set for {0} seconds from now```'
    await ctx.send(fmt.format(expire_seconds))


@bot.command()
async def listroles(ctx):
    guild = ctx.guild
    output="```Roles available:\n"
    for role in guild.roles:
        if (role.name != "@everyone"):
            output+="\t\""+role.name+"\"\n"
    output+="```"
    await ctx.send(output)

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
                if ctx.valid and testenv.TestCog.check_test_environment(ctx):
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
    print("ZA WARUDOOO!!!!")

@bot.command()
async def urban(ctx, queryString):
    url = 'http://api.urbandictionary.com/v0/define?term=%s' % queryString
    res = urllib.request.urlopen(url)
    data = json.loads(res.read().decode())

    data = data['list']
    str = ''
    if not data:
        await ctx.send("```lul 404.\nYou seached something stupid didnt you?```")
        return
    else:
        str = data[1]['definition']
        link = "\n <" + data[1]['permalink'] + ">"
        await ctx.send("```" + str + "```" + "\n*Link* " + link)

if __name__ == '__main__':
    bot.load_extension('testenv')

bot.run(TOKEN)
