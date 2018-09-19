from discord.ext import commands
import discord
import logging
from commands_to_load.Paginate import paginate

logger = logging.getLogger('wall_e')

class RoleCommands():

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def newrole(self, ctx, roleToAdd):
        logger.info("[RoleCommands newrole()] "+str(ctx.message.author)+" called newrole with following argument: roleToAdd="+roleToAdd)
        roleToAdd = roleToAdd.lower()
        guild = ctx.guild
        for role in guild.roles:
            if role.name == roleToAdd:
                await ctx.send("```" + "Role '" + roleToAdd + "' exists. Calling .iam " + roleToAdd +" will add you to it." + "```")
                logger.error("[RoleCommands newrole()] "+roleToAdd+" already exists")
                return
        role = await guild.create_role(name=roleToAdd)
        await role.edit(mentionable=True)
        logger.info("[RoleCommands newrole()] "+str(roleToAdd)+" created and is set to mentionable")
        await ctx.send("```" + "You have successfully created role '" + roleToAdd + "'. Calling .iam " + roleToAdd + " will add you to it." + "```")

    @commands.command()
    async def deleterole(self, ctx, roleToDelete):
        logger.info("[RoleCommands deleterole()] "+str(ctx.message.author)+" called deleterole with role "+str(roleToDelete)+".")
        roleToDelete = roleToDelete.lower()
        role = discord.utils.get(ctx.guild.roles, name=roleToDelete)
        if role == None:
            logger.info("[RoleCommands deleterole()] role that user wants to delete doesnt seem to exist.")
            await ctx.send("```" + "Role '" + roleToDelete + "' does not exist." + "```")
            return
        membersOfRole = role.members
        if not membersOfRole:
            deleteRole = await role.delete()
            logger.info("[RoleCommands deleterole()] no members were detected, role has been deleted.")
            await ctx.send("```" + "Role '" + roleToDelete + "' deleted." + "```")
        else:
            logger.info("[RoleCommands deleterole()] members were detected, role can't be deleted.")
            await ctx.send("```" + "Role '" + roleToDelete + "' has members. Cannot delete." + "```")

    @commands.command()
    async def iam(self, ctx, roleToAdd):
        logger.info("[RoleCommands iam()] "+str(ctx.message.author)+" called iam with role "+str(roleToAdd))
        roleToAdd = roleToAdd.lower()
        role = discord.utils.get(ctx.guild.roles, name=roleToAdd)
        if role == None:
            logger.error("[RoleCommands iam()] role doesnt exist.")
            await ctx.send("```" + "Role '" + roleToAdd + "' does not exist. Calling .newrole " + roleToAdd +" will create it." + "```")
            return
        user = ctx.message.author
        membersOfRole = role.members
        if user in membersOfRole:
            logger.error("[RoleCommands iam()] " + str(user) + " was already in the role " + str(roleToAdd) + ".")
            await ctx.send("```" + "You were already in the role '" + roleToAdd + "'." + "```")
        else:
            await user.add_roles(role)
            logger.info("[RoleCommands iam()] user " + str(user) + " added to role " + str(roleToAdd) + ".")
            await ctx.send("```" + "You have successfully been added to role '" + roleToAdd + "'." + "```")
        
    @commands.command()
    async def iamn(self, ctx, roleToRemove):
        logger.info("[RoleCommands iamn()] "+str(ctx.message.author)+" called iamn with role "+str(roleToRemove))
        roleToRemove = roleToRemove.lower()
        role = discord.utils.get(ctx.guild.roles, name=roleToRemove)
        if role == None:
            logger.error("[RoleCommands iam()] role doesnt exist.")
            await ctx.send("```" + "Role '" + roleToRemove + "' does not exist." + "```")
            return
        membersOfRole = role.members
        user = ctx.message.author
        if user in membersOfRole:
            await user.remove_roles(role)
            await ctx.send("```" + "You have successfully been removed from role '" + roleToRemove + "'." + "```")
            logger.info("[RoleCommands iamn()] " + str(user) + " has been removed from role " + str(roleToRemove) )
        else:
            await ctx.send("```" + "You don't seem to be in the role " +roleToRemove+".```")
            logger.error("[RoleCommands iamn()] " + str(user) + " wasnt in the role " + str(roleToRemove) )
        
        

    @commands.command()
    async def whois(self, ctx, roleToCheck):
        logger.info("[RoleCommands whois()] "+str(ctx.message.author)+" called whois with role "+str(roleToCheck))
        memberString = ""
        role = discord.utils.get(ctx.guild.roles, name=roleToCheck)
        if role == None:
            await ctx.send("```" + "Role '" + roleToCheck + "' does not exist." + "```")
            logger.error("[RoleCommands whois()] role "+str(roleToCheck) + " doesnt exist")
            return
        membersOfRole = role.members
        if not membersOfRole:
            logger.error("[RoleCommands whois()] there are no members in the role "+str(roleToCheck))
            await ctx.send("```" + "No members in role '" + roleToCheck + "'." + "```")
            return
        for members in membersOfRole:
            name = members.nick or members.name
            memberString += name + "\n"
        logger.info("[RoleCommands whois()] following members were found in the role: "+str(memberString))
        await ctx.send("Members belonging to role `" + roleToCheck + "`:\n" + "```\n" + memberString + "```")

    @commands.command()
    async def roles(self, ctx):
        logger.info("[Misc roles()] roles command detected from user "+str(ctx.message.author))
        guild = ctx.guild
        rolesList = []
        selfAssignRoles = []
        for role in guild.roles:
            if role.name != "@everyone" and role.name[0] == role.name[0].lower():
                selfAssignRoles.append(str(role.name))
        logger.info("[Misc roles()] rolesList array populated with the roles extracted from \"guild.roles\"")

        selfAssignRoles = sorted(selfAssignRoles, key=str.lower)
        logger.info("[Misc roles()] roles in arrays sorted alphabetically")

        for role in selfAssignRoles:
            rolesList.append(role)

        await paginate(bot=self.bot,title="Self-Assignable Roles" ,ctx=ctx,listToPaginate=rolesList, numOfPageEntries=10)

    @commands.command()
    async def Roles(self, ctx):
        logger.info("[Misc Roles()] roles command detected from user "+str(ctx.message.author))
        guild = ctx.guild
        rolesList = []
        assignedRoles = []
        for role in guild.roles:
            if role.name != "@everyone" and role.name[0] != role.name[0].lower():
                assignedRoles.append(str(role.name))

        logger.info("[Misc Roles()] rolesList array populated with the roles extracted from \"guild.roles\"")

        assignedRoles = sorted(assignedRoles, key=str.lower)
        logger.info("[Misc Roles()] roles in arrays sorted alphabetically")

        for role in assignedRoles:
            rolesList.append(role)

        await paginate(bot=self.bot,title="Mod/Exec/XP Assigned Roles" ,ctx=ctx,listToPaginate=rolesList, numOfPageEntries=10)
def setup(bot):
    bot.add_cog(RoleCommands(bot))