import os
import discord
from discord.ext import commands

TOKEN = os.environ['TOKEN']

bot = commands.Bot(command_prefix='.')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.command()
async def ping(ctx):
    await ctx.send('pong!')
	
@bot.command()
async def echo(ctx, arg):
    await ctx.send(arg)
    
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
async def iamn(ctx, roleToAdd):
    roleToAdd = roleToAdd.lower()
    role = discord.utils.get(ctx.guild.roles, name=roleToAdd)
    if role == None:
        await ctx.send("```" + "Role '" + roleToAdd + "' does not exist." + "```")
        return
    user = ctx.message.author
    await user.remove_roles(role)
    await ctx.send("```" + "You have successfully been removed from role '" + roleToAdd + "'." + "```")

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
        memberString += members.name + "\n"
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

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        fmt = '```Missing argument: {0}```'
        await ctx.send(fmt.format(error.param))

bot.run(TOKEN)