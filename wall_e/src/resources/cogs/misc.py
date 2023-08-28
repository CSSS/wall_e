import asyncio
import re
import urllib
from io import BytesIO

import aiohttp
import discord
import wolframalpha
from discord import app_commands
from discord.ext import commands
from matplotlib import pyplot as plt

from resources.utilities.embed import embed
from resources.utilities.file_uploading import start_file_uploading
from resources.utilities.list_of_perms import get_list_of_user_permissions
from resources.utilities.paginate import paginate_embed
from resources.utilities.setup_logger import Loggers


def render_latex(formula, fontsize=12, dpi=300, format_='svg'):
    """Renders LaTeX formula into image.
    """
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, f'${formula}$', fontsize=fontsize, color='white')
    buffer_ = BytesIO()
    fig.savefig(
        buffer_, dpi=dpi, transparent=True, format=format_, bbox_inches='tight', pad_inches=0.0, facecolor='black'
    )
    plt.close(fig)
    return buffer_.getvalue()


class Misc(commands.Cog):

    def __init__(self, bot, config, bot_channel_manager):
        log_info = Loggers.get_logger(logger_name="Misc")
        self.logger = log_info[0]
        self.debug_log_file_absolute_path = log_info[1]
        self.error_log_file_absolute_path = log_info[2]
        self.bot = bot
        self.session = aiohttp.ClientSession(loop=bot.loop)
        self.config = config
        self.guild = None
        self.bot_channel_manager = bot_channel_manager
        self.wolframClient = wolframalpha.Client(self.config.get_config_value('basic_config', 'WOLFRAM_API_TOKEN'))
        self.help_dict = self.config.get_help_json()

    @commands.Cog.listener(name="on_ready")
    async def get_guild(self):
        self.guild = self.bot.guilds[0]

    @commands.Cog.listener(name="on_ready")
    async def upload_debug_logs(self):
        if self.config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, self.bot, self.config, self.debug_log_file_absolute_path, "misc_debug"
            )

    @commands.Cog.listener(name="on_ready")
    async def upload_error_logs(self):
        if self.config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, self.bot, self.config, self.error_log_file_absolute_path, "misc_error"
            )

    @commands.command()
    async def poll(self, ctx, *questions):
        self.logger.info(f"[Misc poll()] poll command detected from user {ctx.message.author}")
        name = ctx.author.display_name
        ava = ctx.author.avatar.url
        if len(questions) > 12:
            self.logger.info("[Misc poll()] was called with too many options.")
            e_obj = await embed(
                self.logger,
                ctx=ctx,
                title='Poll Error',
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description='Please only submit a maximum of 11 options for a multi-option question.'
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)
            await ctx.message.delete()
            return
        elif len(questions) == 1:
            self.logger.info("[Misc poll()] yes/no poll being constructed.")
            e_obj = await embed(self.logger, ctx=ctx, title='Poll', author=name, avatar=ava, description=questions[0])
            if e_obj is not False:
                post = await ctx.send(embed=e_obj)
                await post.add_reaction(u"\U0001F44D")
                await post.add_reaction(u"\U0001F44E")
                self.logger.info("[Misc poll()] yes/no poll constructed and sent to server.")
            await ctx.message.delete()
            return
        if len(questions) == 2:
            self.logger.info("[Misc poll()] poll with only 2 arguments detected.")
            e_obj = await embed(
                self.logger,
                ctx=ctx,
                title='Poll Error',
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description='Please submit at least 2 options for a multi-option question.'
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)
            await ctx.message.delete()
            return
        elif len(questions) == 0:
            self.logger.info("[Misc poll()] poll with no arguments detected.")
            e_obj = await embed(
                self.logger,
                ctx=ctx,
                title='Usage',
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description='.poll <Question> [Option A] [Option B] ...'
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)
            await ctx.message.delete()
            return
        else:
            self.logger.info("[Misc poll()] multi-option poll being constructed.")
            questions = list(questions)
            option_string = "\n"
            numbers_emoji = [":zero:", ":one:", ":two:", ":three:", ":four:", ":five:", ":six:", ":seven:", ":eight:",
                             ":nine:", ":keycap_ten:"]
            numbers_unicode = [u"0\u20e3", u"1\u20e3", u"2\u20e3", u"3\u20e3", u"4\u20e3", u"5\u20e3", u"6\u20e3",
                               u"7\u20e3", u"8\u20e3", u"9\u20e3", u"\U0001F51F"]
            question = questions.pop(0)
            options = 0
            for m, n in zip(numbers_emoji, questions):
                option_string += f"{m}: {n}\n"
                options += 1

            content = [['Options:', option_string]]
            e_obj = await embed(
                self.logger, ctx=ctx, title='Poll:', author=name, avatar=ava, description=question, content=content
            )
            if e_obj is not False:
                poll_post = await ctx.send(embed=e_obj)
                self.logger.info("[Misc poll()] multi-option poll message contructed and sent.")

                for i in range(0, options):
                    await poll_post.add_reaction(numbers_unicode[i])
                self.logger.info("[Misc poll()] reactions added to multi-option poll message.")
            await ctx.message.delete()

    @commands.command()
    async def urban(self, ctx, *arg):
        self.logger.info("[Misc urban()] urban command detected "
                         f"from user {ctx.message.author} with argument =\"{arg}\"")
        query_string = urllib.parse.urlencode({'term': " ".join(arg)})
        url = f'http://api.urbandictionary.com/v0/define?{query_string}'
        self.logger.info(f"[Misc urban()] following url  constructed for get request =\"{url}\"")
        async with self.session.get(url) as res:
            data = ''
            if res.status == 200:
                self.logger.info("[Misc urban()] Get request successful")
                data = await res.json()
            else:
                self.logger.info(f"[Misc urban()] Get request failed resulted in {res.status}")
            data = data['list']
            if not data:
                self.logger.info("[Misc urban()] sending message indicating 404 result")
                e_obj = await embed(
                    self.logger,
                    ctx=ctx,
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
                self.logger.info("[Misc urban()] constructing "
                                 f"embed object with definition of \"{' '.join(arg)}\"")
                urban_url = f'https://www.urbandictionary.com/define.php?{query_string}'
                # truncate to fit in embed, field values must be 1024 or fewer in length
                definition = (
                        f'{data[0]["definition"][:1021]}...' if len(data[0]['definition']) > 1024
                        else data[0]['definition'])
                content = [
                    ['Definition', definition],
                    ['Link', f'[here]({urban_url})']
                ]
                e_obj = await embed(
                    self.logger,
                    ctx=ctx,
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
        self.logger.info("[Misc wolfram()] wolfram command detected "
                         f"from user {ctx.message.author} with argument =\"{arg}\"")
        self.logger.info("[Misc wolfram()] URL being contructed")
        command_url = arg.replace("+", "%2B")
        command_url = command_url.replace("(", "%28")
        command_url = command_url.replace(")", "%29")
        command_url = command_url.replace("[", "%5B")
        command_url = command_url.replace("]", "%5D")
        command_url = command_url.replace(" ", "+")
        wolfram_url = f'https://www.wolframalpha.com/input/?i={command_url}'
        self.logger.info(f"[Misc wolfram()] querying WolframAlpha for {arg}")
        res = self.wolframClient.query(arg)
        try:
            content = [
                ['Results from Wolfram Alpha', f"`{next(res.results).text}`\n\n[Link]({wolfram_url})"]]
            e_obj = await embed(
                self.logger,
                ctx=ctx,
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                colour=0xdd1100,
                content=content
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)
                self.logger.info(f"[Misc wolfram()] result found for {arg}")
        except (AttributeError, StopIteration):
            content = [
                ['Results from Wolfram Alpha', f"No results found. :thinking: \n\n[Link]({wolfram_url})"],
            ]
            e_obj = await embed(
                self.logger,
                ctx=ctx,
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                colour=0xdd1100,
                content=content
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)
                self.logger.error(f"[Misc wolfram()] result NOT found for {arg}")

    @commands.command()
    async def emojispeak(self, ctx, *args):
        self.logger.info("[Misc emojispeak()] emojispeak command "
                         f"detected from user {ctx.message.author} with argument =\"{args}\"")
        num_arr = [":zero:", ":one:", ":two:", ":three:", ":four:", ":five:", ":six:", ":seven:", ":eight:", ":nine:"]
        output = ""
        for word in args:
            # If the current word is a custom server emoji, just output it
            if re.match(r'<:\w*:\d*>', word):
                output += word
            elif re.match(r':*:', word):
                self.logger.info("[Misc emojispeak()] was called with a non-server emoji.")
                e_obj = await embed(
                    self.logger,
                    ctx=ctx,
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
                            output += f":regional_indicator_{char.lower()}:"
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
        self.logger.info(f"[Misc emojispeak()] deleting {ctx.message}")
        await ctx.message.delete()
        self.logger.info(f"[Misc emojispeak()] sending {ctx.author.mention} says {output}")
        await ctx.send(f"{ctx.author.mention} says {output}")

    async def general_description(self, ctx):
        number_of_commands_per_page = 5
        self.logger.info(f"[Misc general_description()] help command detected from {ctx.message.author}")
        user_roles = [role.name for role in sorted(ctx.author.roles, key=lambda x: int(x.position), reverse=True)]
        self.logger.info(f"[Misc general_description()] user_roles : {user_roles}")
        user_perms = await get_list_of_user_permissions(self.logger, ctx)
        self.logger.info(f"[Misc general_description()] user_perms : {user_perms}")
        description_to_embed = [""]
        number_of_command_added_in_current_page, current_page = 0, 0
        class_in_previous_command = ""
        for command, command_info in self.help_dict.items():
            if command_info['access'] == "roles":
                shared_roles = set(user_roles).intersection(command_info[command_info['access']])
                if len(shared_roles) > 0:
                    self.logger.info("[Misc general_description()] "
                                     f"adding {command} to page {current_page} of the description_to_embed")
                    if class_in_previous_command != command_info['class'] and 'Bot_manager' in user_roles:
                        description_to_embed[current_page] += f"**Class: {command_info['class']}**:\n"
                    if class_in_previous_command == command_info['class'] and \
                            number_of_command_added_in_current_page == 0 and 'Bot_manager' in user_roles:
                        description_to_embed[current_page] += (
                            f"**Class: {command_info['class']}** [Cont'd]:\n"
                            )
                    class_in_previous_command = command_info['class']
                    aliases = command_info['aliases'].copy()
                    aliases.append(command)
                    description_to_embed[current_page] += (
                        f"{'/'.join(aliases)} - {command_info['description'][0]}\n\n"
                    )
                    number_of_command_added_in_current_page += 1
                    if number_of_command_added_in_current_page == number_of_commands_per_page:
                        description_to_embed.append("")
                        current_page += 1
                        number_of_command_added_in_current_page = 0
            elif command_info['access'] == "permissions":
                shared_perms = set(user_perms).intersection(command_info[command_info['access']])
                if len(shared_perms) > 0:
                    self.logger.info("[Misc general_description()] "
                                     f"adding {command} to page {current_page} of the description_to_embed")
                    if class_in_previous_command != command_info['class'] and 'Bot_manager' in user_roles:
                        description_to_embed[current_page] += f"**Class: {command_info['class']}**:\n"
                    if class_in_previous_command == command_info['class'] and \
                            number_of_command_added_in_current_page == 0 and 'Bot_manager' in user_roles:
                        description_to_embed[current_page] += (
                            f"**Class: {command_info['class']}** [Cont'd]:\n"
                        )
                    aliases = command_info['aliases'].copy()
                    aliases.append(command)
                    description_to_embed[current_page] += (
                        f"{'/'.join(aliases)} - {command_info['description'][0]}\n\n"
                    )
                    number_of_command_added_in_current_page += 1
                    if number_of_command_added_in_current_page == number_of_commands_per_page:
                        description_to_embed.append("")
                        current_page += 1
                        number_of_command_added_in_current_page = 0
            else:
                self.logger.info(f"[Misc general_description()] {command} has a wierd "
                                 f"access level of {command_info['access']}....not sure how to handle "
                                 "it so not adding it to the description_to_embed")
        self.logger.info("[Misc general_description()] transfer successful")
        await paginate_embed(self.logger, self.bot, self.config, description_to_embed, title="Help Page", ctx=ctx)

    async def specific_description(self, ctx, command):
        self.logger.info(f"[Misc specific_description()] invoked by user {command} for "
                         "command ")
        command_being_searched_for = f"{command[0]}"
        command_info_for_searched_command = ""
        if command_being_searched_for in self.help_dict:
            command_info_for_searched_command = self.help_dict[command_being_searched_for]
        for command, command_info in self.help_dict.items():
            if command_being_searched_for in command_info['aliases']:
                command_being_searched_for = command
                command_info_for_searched_command = command_info
                break
        if command_info_for_searched_command != "":
            self.logger.info(
                "[Misc specific_description()] loading the "
                f"entry for command {command_being_searched_for} "
                f":\n\n{command_info_for_searched_command}"
            )
            descriptions = ""
            for description in command_info_for_searched_command['description']:
                descriptions += f"{description}\n\n"
            descriptions += "\n\nExample:\n"
            descriptions += "\n".join(command_info_for_searched_command['example'])
            e_obj = await embed(
                self.logger,
                ctx=ctx,
                title=f"Man Entry for {command_being_searched_for}",
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description=descriptions
            )
            if e_obj is not False:
                msg = await ctx.send(content=None, embed=e_obj)
                self.logger.info("[Misc specific_description()] embed created and sent for "
                                 f"command {command}")
                await msg.add_reaction('✅')
                self.logger.info("[Misc specific_description()] reaction added to message")

                def check_reaction(reaction, user):
                    if not user.bot:  # just making sure the bot doesnt take its own reactions
                        # into consideration
                        e = f"{reaction.emoji}"
                        self.logger.info("[Misc specific_description()] "
                                         f"reaction {e} detected from {user}")
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
                        self.logger.info("[Misc specific_description()] "
                                         "timed out waiting for the user's reaction.")
                    if user_reacted:
                        if '✅' == user_reacted[0].emoji:
                            self.logger.info("[Misc specific_description()] user indicates they are done with the "
                                             "roles command, deleting roles message")
                            await msg.delete()
                            return
                    else:
                        self.logger.info("[Misc specific_description()] deleting message")
                        await msg.delete()
                        return

    @commands.command(aliases=['man'])
    async def help(self, ctx, *arg):
        await ctx.send("     help me.....")
        self.logger.info("[Misc help()] help command detected "
                         f"from {ctx.message.author} with the argument {arg}")
        if len(arg) == 0:
            await self.general_description(ctx)
        else:
            await self.specific_description(ctx, arg)

    @app_commands.command(name="tex", description="draws a mathematical formula")
    @app_commands.describe(formula="formula to draw out")
    async def tex(self, interaction: discord.Interaction, formula: str):
        # created using below links:
        # https://stackoverflow.com/a/31371907
        # https://stackoverflow.com/a/57472241
        image_bytes = render_latex(formula, fontsize=10, dpi=200, format_='png')
        with open('formula.png', 'wb') as image_file:
            image_file.write(image_bytes)
        await interaction.response.send_message(file=discord.File('formula.png'))
        self.logger.info(f"[Misc tex()] formula created and send for [{formula}]")

    async def cog_unload(self) -> None:
        await self.session.close()
        await super().cog_unload()
