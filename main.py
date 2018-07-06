import discord
from discord.ext import commands

TOKEN = 'YOUR_TOKEN_HERE'

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
async def roles(ctx):
    roles = ctx.guild.roles
    await ctx.send(roles)
    
@bot.command()
async def newrole(ctx, roleToAdd):
    guild = ctx.guild
    for role in guild.roles:
        if role.name == roleToAdd:
            await ctx.send("```" + "Role '" + roleToAdd + "' exists. Calling .iam " + roleToAdd +" will add you to it." + "```")
            return
    await guild.create_role(name=roleToAdd)
    await ctx.send("```" + "You have successfully created role '" + roleToAdd + "'. Calling .iam " + roleToAdd + " will add you to it." + "```")
    
@bot.command()
async def iam(ctx, roleToAdd):
    role = discord.utils.get(ctx.guild.roles, name=roleToAdd)
    if role == None:
        await ctx.send("```" + "Role '" + roleToAdd + "' does not exist. Calling .newrole " + roleToAdd +" will create it." + "```")
        return
    user = ctx.message.author
    await user.add_roles(role)
    await ctx.send("```" + "You have successfully been added to role '" + roleToAdd + "'." + "```")
    
@bot.command()
async def iamn(ctx, roleToAdd):
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
    await ctx.send("```" + "Members belonging to role '" + roleToCheck + "':\n" + memberString + "```")

bot.run(TOKEN)