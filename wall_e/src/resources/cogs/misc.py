from discord.ext import commands
import logging
import aiohttp
from resources.utilities.embed import embed
from resources.utilities.paginate import paginateEmbed
from resources.utilities.list_of_perms import getListOfUserPerms
import json
import wolframalpha
# import discord.client
import urllib
import asyncio
import re

logger = logging.getLogger('wall_e')


def getClassName():
    return "Misc"


class Misc(commands.Cog):

    def __init__(self, bot, config):
        self.bot = bot
        self.session = aiohttp.ClientSession(loop=bot.loop)
        self.config = config
        self.wolframClient = wolframalpha.Client(self.config.get_config_value('wolfram', 'WOLFRAM_API_TOKEN'))

    @commands.command()
    async def poll(self, ctx, *questions):
        logger.info("[Misc poll()] poll command detected from user {}".format(ctx.message.author))
        name = ctx.author.display_name
        ava = ctx.author.avatar_url
        if len(questions) > 12:
            logger.info("[Misc poll()] was called with too many options.")
            eObj = await embed(
                ctx,
                title='Poll Error',
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description='Please only submit a maximum of 11 options for a multi-option question.'
            )
            if eObj is not False:
                await ctx.send(embed=eObj)
            return
        elif len(questions) == 1:
            logger.info("[Misc poll()] yes/no poll being constructed.")
            eObj = await embed(ctx, title='Poll', author=name, avatar=ava, description=questions[0])
            if eObj is not False:
                post = await ctx.send(embed=eObj)
                await post.add_reaction(u"\U0001F44D")
                await post.add_reaction(u"\U0001F44E")
                logger.info("[Misc poll()] yes/no poll constructed and sent to server.")
            return
        if len(questions) == 2:
            logger.info("[Misc poll()] poll with only 2 arguments detected.")
            eObj = await embed(
                ctx,
                title='Poll Error',
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description='Please submit at least 2 options for a multi-option question.'
            )
            if eObj is not False:
                await ctx.send(embed=eObj)
            return
        elif len(questions) == 0:
            logger.info("[Misc poll()] poll with no arguments detected.")
            eObj = await embed(
                ctx,
                title='Usage',
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description='.poll <Question> [Option A] [Option B] ...'
            )
            if eObj is not False:
                await ctx.send(embed=eObj)
            return
        else:
            logger.info("[Misc poll()] multi-option poll being constructed.")
            questions = list(questions)
            optionString = "\n"
            numbersEmoji = [":zero:", ":one:", ":two:", ":three:", ":four:", ":five:", ":six:", ":seven:", ":eight:",
                            ":nine:", ":keycap_ten:"]
            numbersUnicode = [u"0\u20e3", u"1\u20e3", u"2\u20e3", u"3\u20e3", u"4\u20e3", u"5\u20e3", u"6\u20e3",
                              u"7\u20e3", u"8\u20e3", u"9\u20e3", u"\U0001F51F"]
            question = questions.pop(0)
            options = 0
            for m, n in zip(numbersEmoji, questions):
                optionString += "{}: {}\n".format(m, n)
                options += 1

            content = [['Options:', optionString]]
            eObj = await embed(ctx, title='Poll:', author=name, avatar=ava, description=question, content=content)
            if eObj is not False:
                pollPost = await ctx.send(embed=eObj)
                logger.info("[Misc poll()] multi-option poll message contructed and sent.")

                for i in range(0, options):
                    await pollPost.add_reaction(numbersUnicode[i])
                logger.info("[Misc poll()] reactions added to multi-option poll message.")

    @commands.command()
    async def urban(self, ctx, *arg):
        logger.info("[Misc urban()] urban command detected "
                    "from user {} with argument =\"{}\"".format(ctx.message.author, arg))
        queryString = urllib.parse.urlencode({'term': " ".join(arg)})
        url = 'http://api.urbandictionary.com/v0/define?{}'.format(queryString)
        logger.info("[Misc urban()] following url  constructed for get request =\"{}\"".format(url))
        async with self.session.get(url) as res:
            data = ''
            if res.status == 200:
                logger.info("[Misc urban()] Get request successful")
                data = await res.json()
            else:
                logger.info("[Misc urban()] Get request failed resulted in {}".format(res.status))
            data = data['list']
            if not data:
                logger.info("[Misc urban()] sending message indicating 404 result")
                eObj = await embed(
                    ctx,
                    title="Urban Results",
                    author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    colour=0xfd6a02,
                    description=":thonk:404:thonk:You searched something dumb didn't you?"
                )
                if eObj is not False:
                    await ctx.send(embed=eObj)
                return
            else:
                logger.info("[Misc urban()] constructing "
                            "embed object with definition of \"{}\"".format(" ".join(arg)))
                urbanUrl = 'https://www.urbandictionary.com/define.php?{}'.format(queryString)
                # truncate to fit in embed, field values must be 1024 or fewer in length
                definition = (
                        '{}...'.format(data[0]['definition'][:1021]) if len(data[0]['definition']) > 1024
                        else data[0]['definition'])
                content = [
                    ['Definition', definition],
                    ['Link', '[here]({})'.format(urbanUrl)]
                ]
                eObj = await embed(
                    ctx,
                    title='Results from Urban Dictionary',
                    author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    colour=0xfd6a02,
                    content=content
                )
                if eObj is not False:
                    await ctx.send(embed=eObj)

    @commands.command()
    async def wolfram(self, ctx, *arg):
        arg = " ".join(arg)
        logger.info("[Misc wolfram()] wolfram command detected "
                    "from user {} with argument =\"{}\"".format(ctx.message.author, arg))
        logger.info("[Misc wolfram()] URL being contructed")
        commandURL = arg.replace("+", "%2B")
        commandURL = commandURL.replace("(", "%28")
        commandURL = commandURL.replace(")", "%29")
        commandURL = commandURL.replace("[", "%5B")
        commandURL = commandURL.replace("]", "%5D")
        commandURL = commandURL.replace(" ", "+")
        wolframURL = 'https://www.wolframalpha.com/input/?i={}'.format(commandURL)
        logger.info("[Misc wolfram()] querying WolframAlpha for {}".format(arg))
        res = self.wolframClient.query(arg)
        try:
            content = [
                ['Results from Wolfram Alpha', "`{}`\n\n[Link]({})".format(next(res.results).text, wolframURL)]]
            eObj = await embed(
                ctx,
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                colour=0xdd1100,
                content=content
            )
            if eObj is not False:
                await ctx.send(embed=eObj)
                logger.info("[Misc wolfram()] result found for {}".format(arg))
        except (AttributeError, StopIteration):
            content = [
                ['Results from Wolfram Alpha', "No results found. :thinking: \n\n[Link]({})".format(wolframURL)], ]
            eObj = await embed(
                ctx,
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                colour=0xdd1100,
                content=content
            )
            if eObj is not False:
                await ctx.send(embed=eObj)
                logger.error("[Misc wolfram()] result NOT found for {}".format(arg))

    @commands.command()
    async def emojispeak(self, ctx, *args):
        logger.info("[Misc emojispeak()] emojispeak command "
                    "detected from user {} with argument =\"{}\"".format(ctx.message.author, args))
        numArr = [":zero:", ":one:", ":two:", ":three:", ":four:", ":five:", ":six:", ":seven:", ":eight:", ":nine:"]
        output = ""
        for word in args:
            # If the current word is a custom server emoji, just output it
            if re.match(r'<:\w*:\d*>', word):
                output += word
            elif re.match(r':*:', word):
                logger.info("[Misc emojispeak()] was called with a non-server emoji.")
                eObj = await embed(
                    ctx,
                    title='EmojiSpeak Error',
                    author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    description='Please refrain from using non-server emoji.'
                )
                if eObj is not False:
                    await ctx.send(embed=eObj)
                return
            else:
                for char in word:
                    # Check if char is ascii
                    try:
                        char.encode('ascii')
                        # If it is not ascii, output plain text char
                    except UnicodeEncodeError:
                        output += char
                        # If it is ascii, handle accordingly
                    else:
                        # If letter, output regional indicator emoji
                        if char.isalpha():
                            output += ":regional_indicator_{}:".format(char.lower())
                        # If number, output number emoji
                        elif char.isdigit():
                            output += numArr[int(char)]
                        # If ?, output ? emoji
                        elif char == '?':
                            output += ":question:"
                        # If !, output ! emoji
                        elif char == '!':
                            output += ":exclamation:"
                        # If any other symbol, output plain text
                        else:
                            output += char
            output += " "
        # Mention the user, and send the emote speak
        logger.info("[Misc emojispeak()] deleting {}".format(ctx.message))
        await ctx.message.delete()
        logger.info("[Misc emojispeak()] sending {} says ".format(ctx.author.mention, output))
        await ctx.send("{} says {}".format(ctx.author.mention, output))

    async def GeneralDescription(self, ctx):
        numberOfCommandsPerPage = 5
        logger.info("[Misc GeneralDescription()] help command detected from {}".format(ctx.message.author))
        logger.info("[Misc GeneralDescription()] attempting to load command info from help.json")
        helpDict = self.config.get_help_json()
        logger.info("[Misc GeneralDescription()] loaded "
                    "commands from help.json=\n{}".format(json.dumps(helpDict, indent=3)))
        user_perms = await getListOfUserPerms(ctx)
        user_roles = [role.name for role in sorted(ctx.author.roles, key=lambda x: int(x.position), reverse=True)]
        descriptionToEmbed = [""]
        x, page = 0, 0
        for entry in helpDict['commands']:
            if entry['access'] == "role":
                for role in entry[entry['access']]:
                    if (role in user_roles or (role == 'public')):
                        if 'Class' in entry['name'] and 'Bot_manager' in user_roles:
                            logger.info("[Misc GeneralDescription()] "
                                        "adding {} to page {} of the descriptionToEmbed".format(entry, page))
                            descriptionToEmbed[page] += "\n**{}**: \n".format(entry['name'])
                        else:
                            logger.info("[Misc GeneralDescription()] "
                                        "adding {} to page {} of the descriptionToEmbed".format(entry, page))
                            descriptionToEmbed[page] += (
                                "*{}* - {}\n\n".format("/".join(entry['name']), entry['description'][0])
                            )
                            x += 1
                            if x == numberOfCommandsPerPage:
                                descriptionToEmbed.append("")
                                page += 1
                                x = 0
            elif entry['access'] == "permissions":
                for permission in entry[entry['access']]:
                    if permission in user_perms:
                        logger.info("[Misc GeneralDescription()] "
                                    "adding {} to page {} of the descriptionToEmbed".format(entry, page))
                        descriptionToEmbed[page] += (
                            "*{}* - {}\n\n".format("/".join(entry['name']), entry['description'][0])
                        )
                        x += 1
                        if x == numberOfCommandsPerPage:
                            descriptionToEmbed.append("")
                            page += 1
                            x = 0
                        break
            else:
                logger.info("[Misc GeneralDescription()] {} has a wierd "
                            "access level of {}....not sure how to handle "
                            "it so not adding it to the descriptionToEmbed".format(entry, entry['access']))
        logger.info("[Misc GeneralDescription()] transfer successful")
        await paginateEmbed(self.bot, ctx, self.config, descriptionToEmbed, title="Help Page")

    async def specificDescription(self, ctx, command):
        helpDict = self.config.get_help_json()
        logger.info("[Misc specificDescription()] invoked by user {} for "
                    "command ".format(command))
        for entry in helpDict['commands']:
            for name in entry['name']:
                if name == command[0]:
                    logger.info("[Misc specificDescription()] loading the "
                                "entry for command {} :\n\n{}".format(command[0], entry))
                    descriptions = ""
                    for description in entry['description']:
                        descriptions += "{}\n\n".format(description)
                    descriptions += "\n\nExample:\n"
                    descriptions += "\n".join(entry['example'])
                    eObj = await embed(
                        ctx,
                        title="Man Entry for {}".format(command[0]),
                        author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                        avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                        description=descriptions
                    )
                    if eObj is not False:
                        msg = await ctx.send(content=None, embed=eObj)
                        logger.info("[Misc specificDescription()] embed created and sent for "
                                    "command {}".format(command[0]))
                        await msg.add_reaction('✅')
                        logger.info("[Misc specificDescription()] reaction added to message")

                        def checkReaction(reaction, user):
                            if not user.bot:  # just making sure the bot doesnt take its own reactions
                                # into consideration
                                e = str(reaction.emoji)
                                logger.info("[Misc specificDescription()] "
                                            "reaction {} detected from {}".format(e, user))
                                return e.startswith(('✅'))

                        userReacted = False
                        while userReacted is False:
                            try:
                                userReacted = await self.bot.wait_for('reaction_add', timeout=20, check=checkReaction)
                            except asyncio.TimeoutError:
                                logger.info("[Misc specificDescription()] "
                                            "timed out waiting for the user's reaction.")
                            if userReacted:
                                if '✅' == userReacted[0].emoji:
                                    logger.info("[Misc specificDescription()] user indicates they are done with the "
                                                "roles command, deleting roles message")
                                    await msg.delete()
                                    return
                            else:
                                logger.info("[Misc specificDescription()] deleting message")
                                await msg.delete()
                                return

    @commands.command(aliases=['man'])
    async def help(self, ctx, *arg):
        await ctx.send("     help me.....")
        logger.info("[Misc help()] help command detected "
                    "from {} with the argument {}".format(ctx.message.author, arg))
        if len(arg) == 0:
            await self.GeneralDescription(ctx)
        else:
            await self.specificDescription(ctx, arg)

    async def __del__(self):
        await self.session.close()
