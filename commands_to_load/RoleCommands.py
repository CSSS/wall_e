from discord.ext import commands
import discord
import logging
from helper_files.Paginate import paginateEmbed
import helper_files.settings as settings
from helper_files.embed import embed
from operator import itemgetter

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
                eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="Role '" + roleToAdd + "' exists. Calling .iam " + roleToAdd +" will add you to it.")
                await ctx.send(embed=eObj)
                logger.info("[RoleCommands newrole()] "+roleToAdd+" already exists")
                return
        role = await guild.create_role(name=roleToAdd)
        await role.edit(mentionable=True)
        logger.info("[RoleCommands newrole()] "+str(roleToAdd)+" created and is set to mentionable")

        eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="You have successfully created role **`" + roleToAdd + "`**.\nCalling `.iam "+roleToAdd+"` will add it to you.")
        await ctx.send(embed=eObj)

    @commands.command()
    async def deleterole(self, ctx, roleToDelete):
        logger.info("[RoleCommands deleterole()] "+str(ctx.message.author)+" called deleterole with role "+str(roleToDelete)+".")
        roleToDelete = roleToDelete.lower()
        role = discord.utils.get(ctx.guild.roles, name=roleToDelete)
        if role == None:
            logger.info("[RoleCommands deleterole()] role that user wants to delete doesnt seem to exist.")
            eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="Role **`" + roleToDelete + "`** does not exist.")
            await ctx.send(embed=eObj)
            return
        membersOfRole = role.members
        if not membersOfRole:
            deleteRole = await role.delete()
            logger.info("[RoleCommands deleterole()] no members were detected, role has been deleted.")
            eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="Role **`" + roleToDelete + "`** deleted.")
            await ctx.send(embed=eObj)
        else:
            logger.info("[RoleCommands deleterole()] members were detected, role can't be deleted.")
            eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="Role **`" + roleToDelete + "`** has members. Cannot delete.")
            await ctx.send(embed=eObj)

    @commands.command()
    async def iam(self, ctx, roleToAdd):
        logger.info("[RoleCommands iam()] "+str(ctx.message.author)+" called iam with role "+str(roleToAdd))
        roleToAdd = roleToAdd.lower()
        role = discord.utils.get(ctx.guild.roles, name=roleToAdd)
        if role == None:
            logger.info("[RoleCommands iam()] role doesnt exist.")
            eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="Role **`" + roleToAdd + "**` doesn't exist.\nCalling .newrole " + roleToAdd)
            await ctx.send(embed=eObj)
            return
        user = ctx.message.author
        membersOfRole = role.members
        if user in membersOfRole:
            logger.info("[RoleCommands iam()] " + str(user) + " was already in the role " + str(roleToAdd) + ".")
            eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="Beep Boop\n You've already got the role dude STAAAHP!!")
            await ctx.send(embed=eObj)
        else:
            await user.add_roles(role)
            logger.info("[RoleCommands iam()] user " + str(user) + " added to role " + str(roleToAdd) + ".")

            if(roleToAdd == 'froshee'):
                eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="**WELCOME TO SFU!!!!**\nYou have successfully been added to role **`" + roleToAdd + "`**.")
            else:
                eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="You have successfully been added to role **`" + roleToAdd + "`**.")
            await ctx.send(embed=eObj)

    @commands.command()
    async def iamn(self, ctx, roleToRemove):
        logger.info("[RoleCommands iamn()] "+str(ctx.message.author)+" called iamn with role "+str(roleToRemove))
        roleToRemove = roleToRemove.lower()
        role = discord.utils.get(ctx.guild.roles, name=roleToRemove)
        if role == None:
            logger.info("[RoleCommands iam()] role doesnt exist.")
            eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="Role **`" + roleToRemove + "`** doesn't exist.")
            await ctx.send(embed=eObj)
            return
        membersOfRole = role.members
        user = ctx.message.author
        if user in membersOfRole:
            await user.remove_roles(role)
            eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="You have successfully been removed from role **`" + roleToRemove + "`**.")
            await ctx.send(embed=eObj)
            logger.info("[RoleCommands iamn()] " + str(user) + " has been removed from role " + str(roleToRemove) )
            # delete role if last person
            membersOfRole = role.members
            if not membersOfRole:
                deleteRole = await role.delete()
                logger.info("[RoleCommands deleterole()] no members were detected, role has been deleted.")
                eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="Role **`" + role.name + "`** deleted.")
                await ctx.send(embed=eObj)
        else:
            eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="Boop Beep??\n You don't have the role, so how am I gonna remove it????")
            await ctx.send(embed=eObj)
            logger.info("[RoleCommands iamn()] " + str(user) + " wasnt in the role " + str(roleToRemove) )



    @commands.command()
    async def whois(self, ctx, roleToCheck):
        logger.info("[RoleCommands whois()] "+str(ctx.message.author)+" called whois with role "+str(roleToCheck))
        memberString = ""
        logString = ""
        role = discord.utils.get(ctx.guild.roles, name=roleToCheck)
        if role == None:
            eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="**`" + roleToCheck + "`** does not exist.")
            await ctx.send(embed=eObj)
            logger.info("[RoleCommands whois()] role "+str(roleToCheck) + " doesnt exist")
            return
        membersOfRole = role.members
        if not membersOfRole:
            logger.info("[RoleCommands whois()] there are no members in the role "+str(roleToCheck))
            eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="No members in role **`" + roleToCheck + "`**.")
            await ctx.send(embed=eObj)
            return
        for members in membersOfRole:
            name = members.display_name
            memberString += name + "\n"
            logString += name + '\t'
        logger.info("[RoleCommands whois()] following members were found in the role: "+str(logString))
        eObj = embed(title="Members belonging to role: `" + roleToCheck + '`', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description=memberString)
        await ctx.send(embed=eObj)

    @commands.command()
    async def roles(self, ctx):
        numberOfRolesPerPage=5
        logger.info("[RoleCommands roles()] roles command detected from user "+str(ctx.message.author))

        #declares and populates selfAssignRoles with all self-assignable roles and how many people are in each role
        selfAssignRoles = []
        for role in ctx.guild.roles:
            if role.name != "@everyone" and role.name[0] == role.name[0].lower():
                numberOfMembers = len(discord.utils.get(ctx.guild.roles, name=str(role.name)).members)
                selfAssignRoles.append((str(role.name),numberOfMembers))

        logger.info("[RoleCommands roles()] selfAssignRoles array populated with the roles extracted from \"guild.roles\"")

        selfAssignRoles.sort(key=itemgetter(0))
        logger.info("[RoleCommands roles()] roles in arrays sorted alphabetically")

        logger.info("[RoleCommands roles()] tranferring array to description array")
        x, currentIndex = 0, 0;
        descriptionToEmbed = ["Roles - Number of People in Role\n"]
        for roles in selfAssignRoles:
            logger.info("len(descriptionToEmbed)="+str(len(descriptionToEmbed))+" currentIndex="+str(currentIndex))
            descriptionToEmbed[currentIndex]+=str(roles[0])+" - "+str(roles[1])+"\n"
            x+=1
            if x == numberOfRolesPerPage: ##this determines how many entries there will be per page
                descriptionToEmbed.append("Roles - Number of People in Role\n")
                currentIndex+=1
                x = 0
        logger.info("[RoleCommands roles()] transfer successful")

        await paginateEmbed(self.bot, ctx,descriptionToEmbed, title="Self-Assignable Roles")

    @commands.command()
    async def Roles(self, ctx):
        numberOfRolesPerPage=5
        logger.info("[Misc Roles()] roles command detected from user "+str(ctx.message.author))

        #declares and populates assignedRoles with all self-assignable roles and how many people are in each role
        assignedRoles = []
        for role in ctx.guild.roles:
            if role.name != "@everyone" and role.name[0] != role.name[0].lower():
                numberOfMembers = len(discord.utils.get(ctx.guild.roles, name=str(role.name)).members)
                assignedRoles.append((str(role.name),numberOfMembers))

        logger.info("[Misc Roles()] assignedRoles array populated with the roles extracted from \"guild.roles\"")

        assignedRoles.sort(key=itemgetter(0))
        logger.info("[Misc Roles()] roles in arrays sorted alphabetically")

        logger.info("[HealthChecks help()] tranferring array to description array")

        x, currentIndex = 0, 0;
        descriptionToEmbed = ["Roles - Number of People in Role\n"]
        for roles in assignedRoles:
            descriptionToEmbed[currentIndex]+=str(roles[0])+" - "+str(roles[1])+"\n"
            x+=1
            if x == numberOfRolesPerPage:
                descriptionToEmbed.append("Roles - Number of People in Role\n")
                currentIndex+=1
                x = 0
        logger.info("[RoleCommands roles()] transfer successful")

        await paginateEmbed(self.bot,ctx,descriptionToEmbed, title="Mod/Exec/XP Assigned Roles")


    @commands.command()
    async def purgeroles(self, ctx):
        logger.info("[Misc purgeroles()] purgeroles command detected from user " + str(ctx.message.author))

        embed = discord.Embed(type = "rich")
        embed.color = discord.Color.blurple()
        embed.set_footer(text="brenfan", icon_url="https://i.imgur.com/vlpCuu2.jpg")

        #getting member instance of the bot
        bot_user = ctx.guild.get_member(ctx.bot.user.id)


        ##determine if bot is able to delete the roles
        sorted_list_of_authors_roles = sorted(bot_user.roles, key = lambda x: int(x.position),reverse=True)
        bot_highestRole = sorted_list_of_authors_roles[0]

        if not (bot_user.guild_permissions.manage_roles or bot_user.guild_permissions.administrator):
            embed.title = "It seems that the bot don't have permissions to delete roles. :("
            await ctx.send(embed=embed)
            return
        logger.info("[Misc purgeroles()] bot's highest role is " + str(bot_highestRole) +" and its ability to delete roles is " +str(bot_delete_roles_perm))
        

        ##determine if user who is calling the command is able to delete the roles
        author_delete_roles=False
        author_highestRole=ctx.author.roles[0]
        print("User permissions manage_roles="+str(ctx.author.guild_permissions.manage_roles)+" or administrator="+str(ctx.author.guild_permissions.administrator))
        for role in ctx.author.roles:
            if author_highestRole < role:
                author_highestRole = role
            if role.permissions.manage_roles or role.permissions.administrator:
                author_delete_roles = True

        if not author_delete_roles:
            embed.title = "You don't have permissions to delete roles. :("
            await ctx.send(embed=embed)
            return
        logger.info("[Misc purgeroles()] user's highest role is " + str(author_highestRole) +" and its ability to delete roles is " +str(author_delete_roles))


        guild = ctx.guild
        softRoles = []
        undeletableRoles = []
        for role in guild.roles:
            if role.name != "@everyone" and role.name == role.name.lower():
                if author_highestRole >= role and bot_highestRole >= role:
                    softRoles.append(role)
                else:
                    undeletableRoles.append(role.name)
        logger.info("[Misc purgeroles()] Located all the empty roles that both the user and the bot can delete")
        logger.info("[Misc purgeroles()] the ones it can't are: "+str(', '.join(undeletableRoles)))

        deleted = []
        for role in softRoles:
            membersInRole = role.members
            if not membersInRole:
                logger.info("[Misc purgeroles()] deleting empty role @" + role.name)
                deleted.append(role.name)
                await role.delete()
                logger.info("[Misc purgeroles()] deleted empty role @" + role.name)


        if not deleted:
            embed.title="No empty roles to delete."
            await ctx.send(embed=embed)
            return
        deleted.sort(key=itemgetter(0))
        description = "\n".join(deleted)
        embed.title = "Purging " + str(len(deleted)) + " empty roles!"

        embed.description = description

        await ctx.send(embed = embed)

def setup(bot):
    bot.add_cog(RoleCommands(bot))
