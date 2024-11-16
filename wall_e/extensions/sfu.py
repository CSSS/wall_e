import asyncio
import html
import json
import re
import time
from typing import Optional

import aiohttp

import discord
from discord import app_commands
from discord.ext import commands

from utilities.global_vars import bot, wall_e_config

from utilities.embed import embed, WallEColour
from utilities.file_uploading import start_file_uploading
from utilities.setup_logger import Loggers


class SFU(commands.Cog):
    def __init__(self):
        log_info = Loggers.get_logger(logger_name="SFU")
        self.logger = log_info[0]
        self.debug_log_file_absolute_path = log_info[1]
        self.warn_log_file_absolute_path = log_info[2]
        self.error_log_file_absolute_path = log_info[3]
        self.logger.info("[SFU __init__()] initializing SFU")
        self.req = aiohttp.ClientSession(loop=bot.loop)
        self.guild = None

    @commands.Cog.listener(name="on_ready")
    async def get_guild(self):
        self.guild = bot.guilds[0]

    @commands.Cog.listener(name="on_ready")
    async def upload_debug_logs(self):
        while self.guild is None:
            await asyncio.sleep(2)
        await start_file_uploading(
            self.logger, self.guild, bot, wall_e_config, self.debug_log_file_absolute_path, "sfu_debug"
        )

    @commands.Cog.listener(name="on_ready")
    async def upload_warn_logs(self):
        while self.guild is None:
            await asyncio.sleep(2)
        await start_file_uploading(
            self.logger, self.guild, bot, wall_e_config, self.warn_log_file_absolute_path,
            "sfu_warn"
        )

    @commands.Cog.listener(name="on_ready")
    async def upload_error_logs(self):
        while self.guild is None:
            await asyncio.sleep(2)
        await start_file_uploading(
            self.logger, self.guild, bot, wall_e_config, self.error_log_file_absolute_path, "sfu_error"
        )

    async def _embed_message(self, interaction: discord.Interaction, title, footer,
                             content: Optional[list] = None, desc: Optional[str] = None):
        e_obj = await embed(
            self.logger, interaction=interaction,
            title=title,
            content=content,
            description=desc,
            colour=WallEColour.ERROR,
            footer_text=footer
        )
        if e_obj is not False:
            await interaction.response.send_message(embed=e_obj)

    async def _split_course(self, course):
        # Check if arg needs to be manually split
        course = course.split(" ")
        if len(course) == 1:
            # split
            crs = re.findall(r'(\d*\D+)', course[0])
            if len(crs) < 2:
                crs = re.split(r'(\d+)', course[0])

            if len(crs) < 2:
                # Bad args
                return None, None, Exception

            course_code = crs[0].lower()
            course_num = crs[1].lower()
        else:
            course_code = course[0].lower()
            course_num = course[1].lower()
        return course_code, course_num, None

    async def _req_data(self, url):
        res = await self.req.get(url)
        status = res.status
        if status == 200:
            data = ''
            while not res.content.at_eof():
                chunk = await res.content.readchunk()
                data += str(chunk[0].decode())
            res = json.loads(data)
        return res, status

    @app_commands.command(name="sfu",
                          description="Show calendar description from the specified course's current semester",
                          )
    @app_commands.describe(course="The course to get the calendar description for")
    async def sfu(self, interaction: discord.Interaction, course: str):
        self.logger.info(f'[SFU sfu()] sfu command detected from user {interaction.user} with arguments: {course}')

        year = time.localtime()[0]
        term = time.localtime()[1]

        if term <= 4:
            term = 'spring'
        elif 5 <= term <= 8:
            term = 'summer'
        else:
            term = 'fall'

        course_code, course_num, error = await self._split_course(course)
        if error is not None:
            content = [['Usage', '`/sfu course:<arg>`', False], ['Example', '`.sfu course:cmpt300`', False]]
            await self._embed_message(interaction, 'Bad Arguments', 'SFU Error', content=content)
            self.logger.debug('[SFU sfu()] bad arguments, command ended')
            return

        url = f'http://www.sfu.ca/bin/wcm/academic-calendar?{year}/{term}/courses/{course_code}/{course_num}'
        self.logger.debug(f'[SFU sfu()] url for get request constructed: {url}')

        data, status = await self._req_data(url)
        if status == 200:
            self.logger.debug('[SFU sfu()] get request successful')
        else:
            self.logger.debug(f'[SFU sfu()] get resulted in {status}')

            desc = (f'Couldn\'t find anything for:\n{year}/{term.upper()}/{course_code.upper()}/{course_num}/\n'
                    f'Make sure you entered the argument correctly')
            await self._embed_message(interaction, 'Results from SFU', 'SFU Error', desc=desc)
            return

        self.logger.debug('[SFU sfu()] parsing json data returned from get request')
        sfu_url = f'http://www.sfu.ca/students/calendar/{year}/{term}/courses/{course_code}/{course_num}.html'
        link = f'[here]({sfu_url})'
        title = 'Results from SFU'
        footer = 'Written by VJ'

        fields = [
            [data['title'], data['description'], False],
            ["URL", link, False]
        ]
        await self._embed_message(interaction, title, footer, content=fields)

        self.logger.debug('[SFU sfu()] out sent to server')
        return

    async def _construct_fields(self, data, info, schedule):
        outline = info['outlinePath'].upper()
        title = info['title']
        try:
            # instructor = data['instructor'][0]['name'] + '\n[' + data['instructor'][0]['email'] + ']'
            instructor = ''
            instructors = data['instructor']
            for prof in instructors:
                instructor += prof['name']
                instructor += f' [{prof["email"]}]\n'
        except Exception:
            instructor = 'TBA'

        # Course schedule info parsing
        crs = ''
        for x in schedule:
            # [LEC] days time, room, campus
            sec_code = f'[{x["sectionCode"]}]'
            days = x['days']
            tme = f'{x["startTime"]}-{x["endTime"]}'
            campus = x['campus']
            crs = f'{crs}{sec_code} {days} {tme}, {campus}\n'

        class_times = crs

        # Exam info
        exam_times = 'TBA'
        room_info = ''
        tim = ''
        date = ''
        try:
            # Course might not have an exam
            tim = f"{data['examSchedule'][0]['startTime']}-{data['examSchedule'][0]['endTime']}"
            date = data['examSchedule'][0]['startDate'].split()
            date = f'{date[0]} {date[1]} {date[2]}'

            exam_times = f'{tim} {date}'

            # Room info much later
            room_info = (
                f"{data['examSchedule'][0]['buildingCode']} {data['schedule']['roomNumber']}, "
                f"{data['examSchedule'][0]['campus']}"
            )
            exam_times += f'\n{room_info}'
        except Exception:
            pass
        # Other details
        # need to cap len for details
        description = data['info']['description']
        try:
            details = html.unescape(data['info']['courseDetails'])
            details = re.sub('<[^<]+?>', '', details)
            if len(details) > 200:
                details = f'{details[:200]}\n(...)'
        except Exception:
            details = 'None'
        try:
            prerequisites = data['info']['prerequisites'] or 'None'
        except Exception:
            prerequisites = 'None'

        try:
            corequisites = data['info']['corequisites']
        except Exception:
            corequisites = ''

        url = f"http://www.sfu.ca/outlines.html?{data['info']['outlinePath']}"
        self.logger.debug(f"[SFU outline()] finished parsing data for: {data['info']['outlinePath']}")
        # Make tuple of the data for the fields
        fields = [
            ['Outline', outline, False],
            ['Title', title, False],
            ['Instructor', instructor, False],
            ['Class Times', class_times, False],
            ['Exam Times', exam_times, False],
            ['Description', description, False],
            ['Details', details, False],
            ['Prerequisites', prerequisites, False]
        ]

        if corequisites:
            fields.append(['Corequisites', corequisites])
        fields.append(['URL', f'[here]({url})'])

        return fields

    @app_commands.command(name="outline", description="Returns outline details of the specified course")
    @app_commands.describe(course="The course to get the outline for")
    @app_commands.describe(term="The course's term to get the outline for")
    @app_commands.describe(section="A way to specify a course's specific section")
    @app_commands.describe(next_term="Will look at the next semester's outline. "
                                     "This will return error if it is not registration time")
    async def outline(self, interaction: discord.Interaction, course: str, term: Optional[str] = None,
                      section: Optional[str] = None, next_term: Optional[bool] = None):
        self.logger.info(
            f'[SFU outline()] outline command detected from user {interaction.user} with arguments: '
            f'course: {course}, term: {term}, section: {section}, next_term: {next_term}'
        )

        usage = [
                ['Usage', '`/outline course:<course> [term:<term> section:<section> next_term:<next>]`\n'
                          '*<term>, <section>, and <next> are optional arguments*\n'
                          'Note: `next_term` is used for course registration purposes and if '
                          'the next semester info isn\'t available it\'ll return an error.', False],
                ['Example', '`/outline course:cmpt310`\n'
                            '`/outline course:cmpt310 term:fall`\n'
                            '`/outline course:cmpt310 section:d200`\n'
                            '`/outline course:cmpt310 term:spring section:d200`\n'
                            '`/outline course:cmpt310 next_term:True`', False]]

        if next_term:
            year = 'registration'
            term = 'registration'
        else:
            year = 'current'
            if term is None or term.lower() not in ['fall', 'spring', 'summer']:
                term = 'current'
            else:
                term = term.lower()

        self.logger.debug('[SFU outline()] parsing args')
        course_code, course_num, error = await self._split_course(course)
        if error is not None:
            await self._embed_message(interaction, 'Bad Arguments', 'SFU Outline Error',
                                      content=usage)
            self.logger.debug('[SFU outline()] bad arguments, command ended')
            return

        # For embedded error messages
        err_desc = (f'Couldn\'t find anything for `{course_code.upper()} {f"{course_num}".upper()}`\n'
                    f'Maybe the course doesn\'t exist? Or isn\'t offered right now.')

        # Set up url for get
        if section is None:
            # get req the section
            url = f'http://www.sfu.ca/bin/wcm/course-outlines?{year}/{term}/{course_code}/{course_num}'
            self.logger.debug(f'[SFU outline()] url for get request constructed: {url}')

            data, status = await self._req_data(url)
            if status == 200:
                self.logger.debug('[SFU outline()] get request successful')

                self.logger.debug('[SFU outline()] parsing section data')
                for x in data:
                    if x['sectionCode'] in ['LEC', 'LAB', 'TUT', 'SEM']:
                        section = x['value']
                        break
            else:
                self.logger.debug(f'[SFU outline()] section get resulted in {status}')
                await self._embed_message(interaction, 'SFU Course Outlines', 'SFU Outline Error',
                                          desc=err_desc)
                return

        url = f'http://www.sfu.ca/bin/wcm/course-outlines?{year}/{term}/{course_code}/{course_num}/{section}'
        self.logger.debug(f'[SFU outline()] url for get constructed: {url}')

        data, status = await self._req_data(url)
        if status == 200:
            self.logger.debug('[SFU outline()] get request successful')
        else:
            self.logger.debug(f'[SFU outline()] section get resulted in {status}')
            await self._embed_message(interaction, 'SFU Course Outlines', 'SFU Outline Error',
                                      desc=err_desc)
            return

        self.logger.debug('[SFU outline()] parsing data from get request')
        try:
            # Main course information
            info = data['info']

            # Course schedule information
            schedule = data['courseSchedule']
        except Exception:
            self.logger.debug('[SFU outline()] info keys didn\'t exist')
            await self._embed_message(interaction, 'SFU Course Outlines', 'SFU Outline Error',
                                      desc=err_desc)
            return

        fields = await self._construct_fields(data, info, schedule)

        await self._embed_message(interaction, 'SFU Outline Results', 'Written by VJ',
                                  content=fields)
        return

    async def cog_unload(self) -> None:
        await self.req.close()
        await super().cog_unload()


async def setup(bot):
    await bot.add_cog(SFU())
