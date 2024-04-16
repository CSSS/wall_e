import asyncio
import json
import re
import urllib
from io import BytesIO

import aiohttp
import discord
import wolframalpha
from discord import app_commands
from discord.ext import commands
from matplotlib import pyplot as plt

from utilities.autocomplete.examples_command import EXAMPLES_AUTO_COMPLETE_MENU_CHOICES
from utilities.global_vars import bot, wall_e_config

from utilities.embed import embed, WallEColour
from utilities.file_uploading import start_file_uploading
from utilities.send import send
from utilities.setup_logger import Loggers


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

    def __init__(self):
        log_info = Loggers.get_logger(logger_name="Misc")
        self.logger = log_info[0]
        self.debug_log_file_absolute_path = log_info[1]
        self.warn_log_file_absolute_path = log_info[2]
        self.error_log_file_absolute_path = log_info[3]
        self.logger.info("[Misc __init__()] initializing Misc")
        self.session = aiohttp.ClientSession(loop=bot.loop)
        self.guild = None
        self.wolframClient = wolframalpha.Client(wall_e_config.get_config_value('basic_config', 'WOLFRAM_API_TOKEN'))
        with open("utilities/slash_command_examples.json") as examples:
            self.slash_command_examples = json.load(examples)

    @commands.Cog.listener(name="on_ready")
    async def get_guild(self):
        self.guild = bot.guilds[0]

    @commands.Cog.listener(name="on_ready")
    async def upload_debug_logs(self):
        while self.guild is None:
            await asyncio.sleep(2)
        await start_file_uploading(
            self.logger, self.guild, bot, wall_e_config, self.debug_log_file_absolute_path, "misc_debug"
        )

    @commands.Cog.listener(name="on_ready")
    async def upload_warn_logs(self):
        while self.guild is None:
            await asyncio.sleep(2)
        await start_file_uploading(
            self.logger, self.guild, bot, wall_e_config, self.warn_log_file_absolute_path,
            "misc_warn"
        )

    @commands.Cog.listener(name="on_ready")
    async def upload_error_logs(self):
        while self.guild is None:
            await asyncio.sleep(2)
        await start_file_uploading(
            self.logger, self.guild, bot, wall_e_config, self.error_log_file_absolute_path, "misc_error"
        )

    @commands.command(
        brief="creates a poll in the channel",
        help=(
            'Doing .poll "question" starts a yes/no poll with the specified question\n'
            'A poll can also be created with multiple options. When choosing multiple options, you can specify up to '
            '12 arguments\n'
            'Arguments:\n'
            '---question: the question to use in the poll\n'
            '---[answer]: an optional answer that the user can vote in favor of via emoji reactions\n\n'
            'Example:\n'
            '.poll "question"\n'
            '.poll "question" "answer1" "answer2" "answer3"\n\n'
        ),
        usage='question [answer] [answer]...'
    )
    async def poll(self, ctx, *questions):
        self.logger.info(f"[Misc poll()] poll command detected from user {ctx.message.author}")
        if len(questions) > 12:
            self.logger.debug("[Misc poll()] was called with too many options.")
            e_obj = await embed(
                self.logger,
                ctx=ctx,
                title='Poll Error',
                author=ctx.me,
                description='Please only submit a maximum of 11 options for a multi-option question.'
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj, reference=ctx.message)
            return
        elif len(questions) == 1:
            self.logger.debug("[Misc poll()] yes/no poll being constructed.")
            e_obj = await embed(
                self.logger, ctx=ctx, title='Poll', author=ctx.author,
                description=questions[0]
            )
            if e_obj is not False:
                post = await ctx.send(embed=e_obj, reference=ctx.message)
                await post.add_reaction(u"\U0001F44D")
                await post.add_reaction(u"\U0001F44E")
                self.logger.debug("[Misc poll()] yes/no poll constructed and sent to server.")
            return
        if len(questions) == 2:
            self.logger.debug("[Misc poll()] poll with only 2 arguments detected.")
            e_obj = await embed(
                self.logger,
                ctx=ctx,
                title='Poll Error',
                author=ctx.me,
                description='Please submit at least 2 options for a multi-option question.'
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj, reference=ctx.message)
            return
        elif len(questions) == 0:
            self.logger.debug("[Misc poll()] poll with no arguments detected.")
            e_obj = await embed(
                self.logger,
                ctx=ctx,
                title='Usage',
                author=ctx.me,
                description='.poll <Question> [Option A] [Option B] ...'
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj, reference=ctx.message)
            return
        else:
            self.logger.debug("[Misc poll()] multi-option poll being constructed.")
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
                self.logger, ctx=ctx, title='Poll:', author=ctx.author,
                description=question,
                content=content
            )
            if e_obj is not False:
                poll_post = await ctx.send(embed=e_obj, reference=ctx.message)
                self.logger.debug("[Misc poll()] multi-option poll message contructed and sent.")

                for i in range(0, options):
                    await poll_post.add_reaction(numbers_unicode[i])
                self.logger.debug("[Misc poll()] reactions added to multi-option poll message.")

    @commands.command(
        brief="returns definition of the search from urban dictionary",
        help=(
            'Arguments:\n'
            '---search query: the string to query urban dictionary with\n\n'
            'Example:\n'
            '---.urban search query\n\n'
        ),
        usage='search query'
    )
    async def urban(self, ctx, *arg):
        self.logger.info("[Misc urban()] urban command detected "
                         f"from user {ctx.message.author} with argument =\"{arg}\"")
        query_string = urllib.parse.urlencode({'term': " ".join(arg)})
        url = f'http://api.urbandictionary.com/v0/define?{query_string}'
        self.logger.debug(f"[Misc urban()] following url  constructed for get request =\"{url}\"")
        async with self.session.get(url) as res:
            data = ''
            if res.status == 200:
                self.logger.debug("[Misc urban()] Get request successful")
                data = await res.json()
            else:
                self.logger.debug(f"[Misc urban()] Get request failed resulted in {res.status}")
            data = data['list']
            if not data:
                self.logger.debug("[Misc urban()] sending message indicating 404 result")
                e_obj = await embed(
                    self.logger,
                    ctx=ctx,
                    title="Urban Results",
                    author=ctx.me,
                    colour=WallEColour.ERROR,
                    description=":thonk:404:thonk:You searched something dumb didn't you?"
                )
                if e_obj is not False:
                    await ctx.send(embed=e_obj, reference=ctx.message)
                return
            else:
                self.logger.debug("[Misc urban()] constructing "
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
                    author=ctx.me,
                    content=content
                )
                if e_obj is not False:
                    await ctx.send(embed=e_obj, reference=ctx.message)

    @commands.command(
        brief="returns the result searching Wolfram Alpha with given query",
        help=(
            'Arguments:\n'
            '---search query: the string to query Wolfram Alpha with\n\n'
            'Example:\n'
            '---.wolfram search query'
        ),
        usage='search query'
    )
    async def wolfram(self, ctx, *arg):
        arg = " ".join(arg)
        self.logger.info("[Misc wolfram()] wolfram command detected "
                         f"from user {ctx.message.author} with argument =\"{arg}\"")
        self.logger.debug("[Misc wolfram()] URL being contructed")
        command_url = arg.replace("+", "%2B")
        command_url = command_url.replace("(", "%28")
        command_url = command_url.replace(")", "%29")
        command_url = command_url.replace("[", "%5B")
        command_url = command_url.replace("]", "%5D")
        command_url = command_url.replace(" ", "+")
        wolfram_url = f'https://www.wolframalpha.com/input/?i={command_url}'
        self.logger.debug(f"[Misc wolfram()] querying WolframAlpha for {arg}")
        res = self.wolframClient.query(arg)
        try:
            content = [
                ['Results from Wolfram Alpha', f"`{next(res.results).text}`\n\n[Link]({wolfram_url})"]]
            e_obj = await embed(
                self.logger,
                ctx=ctx,
                author=ctx.me,
                content=content
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj, reference=ctx.message)
                self.logger.debug(f"[Misc wolfram()] result found for {arg}")
        except (AttributeError, StopIteration):
            content = [
                ['Results from Wolfram Alpha', f"No results found. :thinking: \n\n[Link]({wolfram_url})"],
            ]
            e_obj = await embed(
                self.logger,
                ctx=ctx,
                author=ctx.me,
                colour=WallEColour.ERROR,
                content=content
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj, reference=ctx.message)
                self.logger.error(f"[Misc wolfram()] result NOT found for {arg}")

    @commands.command(
        brief="returns the user's input in emoji format",
        help=(
            'Arguments:\n'
            '---the message: the message to convert to emoji format\n\n'
            'Example:\n'
            '---.emojispeak wall_e is best'
        ),
        usage='the message'
    )
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
                self.logger.debug("[Misc emojispeak()] was called with a non-server emoji.")
                e_obj = await embed(
                    self.logger,
                    ctx=ctx,
                    title='EmojiSpeak Error',
                    author=ctx.me,
                    description='Please refrain from using non-server emoji.'
                )
                if e_obj is not False:
                    await ctx.send(embed=e_obj, reference=ctx.message)
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
        self.logger.debug(f"[Misc emojispeak()] deleting {ctx.message}")
        await ctx.message.delete()
        self.logger.debug(f"[Misc emojispeak()] sending {ctx.author.mention} says {output}")
        await send(self.logger, ctx, content=f"{ctx.author.mention} says {output}")

    @app_commands.command(name="tex", description="Draws a mathematical formula using latex markdown")
    @app_commands.describe(formula="formula to draw out")
    async def tex(self, interaction: discord.Interaction, formula: str):
        # created using below links:
        # https://stackoverflow.com/a/31371907
        # https://stackoverflow.com/a/57472241
        self.logger.info("[Misc tex()] tex command detected "
                         f"from user {interaction.user} with formula =\"{formula}\"")
        image_bytes = render_latex(formula, fontsize=10, dpi=200, format_='png')
        with open('formula.png', 'wb') as image_file:
            image_file.write(image_bytes)
        await interaction.response.send_message(file=discord.File('formula.png'))
        self.logger.debug(f"[Misc tex()] formula created and send for [{formula}]")

    @app_commands.command(name="examples", description="show examples of how to call various wall_e slash commands")
    @app_commands.describe(slash_command="wall_e slash command to get example for")
    @app_commands.choices(
        slash_command=[
            app_commands.Choice(name=name, value=value)
            for name, value in EXAMPLES_AUTO_COMPLETE_MENU_CHOICES.items()
        ]
    )
    async def examples(self, interaction: discord.Interaction, slash_command: str):
        if slash_command not in list(EXAMPLES_AUTO_COMPLETE_MENU_CHOICES.values()):
            self.logger.debug(f"[Misc examples()] invalid choice of {slash_command} detected")
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user,
                description=f"Invalid choice **`{slash_command}`** specified. Please select from the list.",
                colour=WallEColour.ERROR
            )
        else:
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user,
                title=self.slash_command_examples[slash_command]['header'],
                description=self.slash_command_examples[slash_command]['description']
            )
        await interaction.response.send_message(embed=e_obj)

    async def cog_unload(self) -> None:
        await self.session.close()
        await super().cog_unload()


async def setup(bot):
    await bot.add_cog(Misc())
