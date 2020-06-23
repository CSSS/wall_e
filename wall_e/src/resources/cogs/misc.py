from discord.ext import commands
import logging
import aiohttp
from resources.utilities.embed import embed
from resources.utilities.paginate import paginate_embed
from resources.utilities.list_of_perms import get_list_of_user_permissions
import wolframalpha
import urllib
import asyncio
import re

logger = logging.getLogger('wall_e')


class Misc(commands.Cog):

    def __init__(self, bot, config):
        self.bot = bot
        self.session = aiohttp.ClientSession(loop=bot.loop)
        self.config = config
        self.wolframClient = wolframalpha.Client(self.config.get_config_value('wolfram', 'WOLFRAM_API_TOKEN'))
        self.help_dict = self.config.get_help_json()

    @commands.command()
    async def poll(self, ctx, *questions):
        logger.info("[Misc poll()] poll command detected from user {}".format(ctx.message.author))
        name = ctx.author.display_name
        ava = ctx.author.avatar_url
        if len(questions) > 12:
            logger.info("[Misc poll()] was called with too many options.")
            e_obj = await embed(
                ctx,
                title='Poll Error',
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description='Please only submit a maximum of 11 options for a multi-option question.'
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)
            return
        elif len(questions) == 1:
            logger.info("[Misc poll()] yes/no poll being constructed.")
            e_obj = await embed(ctx, title='Poll', author=name, avatar=ava, description=questions[0])
            if e_obj is not False:
                post = await ctx.send(embed=e_obj)
                await post.add_reaction(u"\U0001F44D")
                await post.add_reaction(u"\U0001F44E")
                logger.info("[Misc poll()] yes/no poll constructed and sent to server.")
            return
        if len(questions) == 2:
            logger.info("[Misc poll()] poll with only 2 arguments detected.")
            e_obj = await embed(
                ctx,
                title='Poll Error',
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description='Please submit at least 2 options for a multi-option question.'
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)
            return
        elif len(questions) == 0:
            logger.info("[Misc poll()] poll with no arguments detected.")
            e_obj = await embed(
                ctx,
                title='Usage',
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description='.poll <Question> [Option A] [Option B] ...'
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)
            return
        else:
            logger.info("[Misc poll()] multi-option poll being constructed.")
            questions = list(questions)
            option_string = "\n"
            numbers_emoji = [":zero:", ":one:", ":two:", ":three:", ":four:", ":five:", ":six:", ":seven:", ":eight:",
                             ":nine:", ":keycap_ten:"]
            numbers_unicode = [u"0\u20e3", u"1\u20e3", u"2\u20e3", u"3\u20e3", u"4\u20e3", u"5\u20e3", u"6\u20e3",
                               u"7\u20e3", u"8\u20e3", u"9\u20e3", u"\U0001F51F"]
            question = questions.pop(0)
            options = 0
            for m, n in zip(numbers_emoji, questions):
                option_string += "{}: {}\n".format(m, n)
                options += 1

            content = [['Options:', option_string]]
            e_obj = await embed(ctx, title='Poll:', author=name, avatar=ava, description=question, content=content)
            if e_obj is not False:
                poll_post = await ctx.send(embed=e_obj)
                logger.info("[Misc poll()] multi-option poll message contructed and sent.")

                for i in range(0, options):
                    await poll_post.add_reaction(numbers_unicode[i])
                logger.info("[Misc poll()] reactions added to multi-option poll message.")

    @commands.command()
    async def urban(self, ctx, *arg):
        logger.info("[Misc urban()] urban command detected "
                    "from user {} with argument =\"{}\"".format(ctx.message.author, arg))
        query_string = urllib.parse.urlencode({'term': " ".join(arg)})
        url = 'http://api.urbandictionary.com/v0/define?{}'.format(query_string)
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
                e_obj = await embed(
                    ctx,
                    title="Urban Results",
                    author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    colour=0xfd6a02,
                    description=":thonk:404:thonk:You searched something dumb didn't you?"
                )
                if e_obj is not False:
                    await ctx.send(embed=e_obj)
                return
            else:
                logger.info("[Misc urban()] constructing "
                            "embed object with definition of \"{}\"".format(" ".join(arg)))
                urban_url = 'https://www.urbandictionary.com/define.php?{}'.format(query_string)
                # truncate to fit in embed, field values must be 1024 or fewer in length
                definition = (
                        '{}...'.format(data[0]['definition'][:1021]) if len(data[0]['definition']) > 1024
                        else data[0]['definition'])
                content = [
                    ['Definition', definition],
                    ['Link', '[here]({})'.format(urban_url)]
                ]
                e_obj = await embed(
                    ctx,
                    title='Results from Urban Dictionary',
                    author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    colour=0xfd6a02,
                    content=content
                )
                if e_obj is not False:
                    await ctx.send(embed=e_obj)

    @commands.command()
    async def wolfram(self, ctx, *arg):
        arg = " ".join(arg)
        logger.info("[Misc wolfram()] wolfram command detected "
                    "from user {} with argument =\"{}\"".format(ctx.message.author, arg))
        logger.info("[Misc wolfram()] URL being contructed")
        command_url = arg.replace("+", "%2B")
        command_url = command_url.replace("(", "%28")
        command_url = command_url.replace(")", "%29")
        command_url = command_url.replace("[", "%5B")
        command_url = command_url.replace("]", "%5D")
        command_url = command_url.replace(" ", "+")
        wolfram_url = 'https://www.wolframalpha.com/input/?i={}'.format(command_url)
        logger.info("[Misc wolfram()] querying WolframAlpha for {}".format(arg))
        res = self.wolframClient.query(arg)
        try:
            content = [
                ['Results from Wolfram Alpha', "`{}`\n\n[Link]({})".format(next(res.results).text, wolfram_url)]]
            e_obj = await embed(
                ctx,
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                colour=0xdd1100,
                content=content
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)
                logger.info("[Misc wolfram()] result found for {}".format(arg))
        except (AttributeError, StopIteration):
            content = [
                ['Results from Wolfram Alpha', "No results found. :thinking: \n\n[Link]({})".format(wolfram_url)], ]
            e_obj = await embed(
                ctx,
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                colour=0xdd1100,
                content=content
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)
                logger.error("[Misc wolfram()] result NOT found for {}".format(arg))

    @commands.command()
    async def emojispeak(self, ctx, *args):
        logger.info("[Misc emojispeak()] emojispeak command "
                    "detected from user {} with argument =\"{}\"".format(ctx.message.author, args))
        num_arr = [":zero:", ":one:", ":two:", ":three:", ":four:", ":five:", ":six:", ":seven:", ":eight:", ":nine:"]
        output = ""
        for word in args:
            # If the current word is a custom server emoji, just output it
            if re.match(r'<:\w*:\d*>', word):
                output += word
            elif re.match(r':*:', word):
                logger.info("[Misc emojispeak()] was called with a non-server emoji.")
                e_obj = await embed(
                    ctx,
                    title='EmojiSpeak Error',
                    author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    description='Please refrain from using non-server emoji.'
                )
                if e_obj is not False:
                    await ctx.send(embed=e_obj)
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
                            output += num_arr[int(char)]
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
        logger.info("[Misc emojispeak()] sending {} says {}".format(ctx.author.mention, output))
        await ctx.send("{} says {}".format(ctx.author.mention, output))

    async def general_description(self, ctx):
        number_of_commands_per_page = 5
        logger.info("[Misc general_description()] help command detected from {}".format(ctx.message.author))
        user_roles = [role.name for role in sorted(ctx.author.roles, key=lambda x: int(x.position), reverse=True)]
        logger.info("user_roles : {}".format(user_roles))
        user_perms = await get_list_of_user_permissions(ctx)
        logger.info("user_perms : {}".format(user_perms))
        description_to_embed = [""]
        number_of_command_added_in_current_page, current_page = 0, 0
        class_in_previous_command = ""
        for command, command_info in self.help_dict.items():
            if command_info['access'] == "roles":
                shared_roles = set(user_roles).intersection(command_info[command_info['access']])
                if len(shared_roles) > 0:
                    logger.info("[Misc general_description()] "
                                "adding {} to page {} of the description_to_embed".format(command, current_page))
                    if class_in_previous_command != command_info['class'] and 'Bot_manager' in user_roles:
                        description_to_embed[current_page] += "**Class: {}**:\n".format(command_info['class'])
                    if class_in_previous_command == command_info['class'] and \
                            number_of_command_added_in_current_page == 0 and 'Bot_manager' in user_roles:
                        description_to_embed[current_page] += (
                            "**Class: {}** [Cont'd]:\n".format(command_info['class'])
                            )
                    class_in_previous_command = command_info['class']
                    aliases = command_info['aliases'].copy()
                    aliases.append(command)
                    description_to_embed[current_page] += (
                        "{} - {}\n\n".format("/".join(aliases), command_info['description'][0])
                    )
                    number_of_command_added_in_current_page += 1
                    if number_of_command_added_in_current_page == number_of_commands_per_page:
                        description_to_embed.append("")
                        current_page += 1
                        number_of_command_added_in_current_page = 0
            elif command_info['access'] == "permissions":
                shared_perms = set(user_perms).intersection(command_info[command_info['access']])
                if len(shared_perms) > 0:
                    logger.info("[Misc general_description()] "
                                "adding {} to page {} of the description_to_embed".format(command, current_page))
                    if class_in_previous_command != command_info['class'] and 'Bot_manager' in user_roles:
                        description_to_embed[current_page] += "**Class: {}**:\n".format(command_info['class'])
                    if class_in_previous_command == command_info['class'] and \
                            number_of_command_added_in_current_page == 0 and 'Bot_manager' in user_roles:
                        description_to_embed[current_page] += (
                            "**Class: {}** [Cont'd]:\n".format(command_info['class'])
                        )
                    aliases = command_info['aliases'].copy()
                    aliases.append(command)
                    description_to_embed[current_page] += (
                        "{} - {}\n\n".format("/".join(aliases), command_info['description'][0])
                    )
                    number_of_command_added_in_current_page += 1
                    if number_of_command_added_in_current_page == number_of_commands_per_page:
                        description_to_embed.append("")
                        current_page += 1
                        number_of_command_added_in_current_page = 0
            else:
                logger.info("[Misc general_description()] {} has a wierd "
                            "access level of {}....not sure how to handle "
                            "it so not adding it to the description_to_embed".format(command, command_info['access']))
        logger.info("[Misc general_description()] transfer successful")
        await paginate_embed(self.bot, ctx, self.config, description_to_embed, title="Help Page")

    async def specific_description(self, ctx, command):
        logger.info("[Misc specific_description()] invoked by user {} for "
                    "command ".format(command))
        command_being_searched_for = "{}".format(command[0])
        command_info_for_searched_command = ""
        if command_being_searched_for in self.help_dict:
            command_info_for_searched_command = self.help_dict[command_being_searched_for]
        for command, command_info in self.help_dict.items():
            if command_being_searched_for in command_info['aliases']:
                command_being_searched_for = command
                command_info_for_searched_command = command_info
                break
        if command_info_for_searched_command != "":
            logger.info(
                "[Misc specific_description()] loading the "
                "entry for command {} :\n\n{}".format(
                    command_being_searched_for,
                    command_info_for_searched_command
                )
            )
            descriptions = ""
            for description in command_info_for_searched_command['description']:
                descriptions += "{}\n\n".format(description)
            descriptions += "\n\nExample:\n"
            descriptions += "\n".join(command_info_for_searched_command['example'])
            e_obj = await embed(
                ctx,
                title="Man Entry for {}".format(command_being_searched_for),
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description=descriptions
            )
            if e_obj is not False:
                msg = await ctx.send(content=None, embed=e_obj)
                logger.info("[Misc specific_description()] embed created and sent for "
                            "command {}".format(command))
                await msg.add_reaction('✅')
                logger.info("[Misc specific_description()] reaction added to message")

                def check_reaction(reaction, user):
                    if not user.bot:  # just making sure the bot doesnt take its own reactions
                        # into consideration
                        e = str(reaction.emoji)
                        logger.info("[Misc specific_description()] "
                                    "reaction {} detected from {}".format(e, user))
                        return e.startswith(('✅'))

                user_reacted = False
                while user_reacted is False:
                    try:
                        user_reacted = await self.bot.wait_for(
                            'reaction_add',
                            timeout=20,
                            check=check_reaction
                        )
                    except asyncio.TimeoutError:
                        logger.info("[Misc specific_description()] "
                                    "timed out waiting for the user's reaction.")
                    if user_reacted:
                        if '✅' == user_reacted[0].emoji:
                            logger.info("[Misc specific_description()] user indicates they are done with the "
                                        "roles command, deleting roles message")
                            await msg.delete()
                            return
                    else:
                        logger.info("[Misc specific_description()] deleting message")
                        await msg.delete()
                        return

    @commands.command(aliases=['man'])
    async def help(self, ctx, *arg):
        await ctx.send("     help me.....")
        logger.info("[Misc help()] help command detected "
                    "from {} with the argument {}".format(ctx.message.author, arg))
        if len(arg) == 0:
            await self.general_description(ctx)
        else:
            await self.specific_description(ctx, arg)

    async def __del__(self):
        await self.session.close()
