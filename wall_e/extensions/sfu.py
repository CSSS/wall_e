import asyncio
import html
import json  # dont need since requests has built in json encoding and decoding
import re
import time

import aiohttp

import discord
from discord import app_commands
from discord.ext import commands

from utilities.global_vars import bot, wall_e_config

from utilities.embed import embed, WallEColour
from utilities.file_uploading import start_file_uploading
from utilities.setup_logger import Loggers
from utilities.paginate import paginate_embed


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

    @commands.command(
        brief="Show calendar description from the specified course's current semester",
        help=(
            "Arguments:\n"
            "---course: semester to get the calendar description for"
        ),
        usage='course'
    )
    async def sfu(self, ctx, *course):
        self.logger.info(f'[SFU sfu()] sfu command detected from user {ctx.message.author} with arguments: {course}')

        if(not course):
            e_obj = await embed(
                self.logger,
                ctx=ctx,
                title='Missing Arguments',
                author=ctx.me,
                colour=WallEColour.ERROR,
                content=[['Usage', '`.sfu <arg>`'], ['Example', '`.sfu cmpt300`']],
                footer_text='SFU Error'
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj, reference=ctx.message)
            self.logger.debug('[SFU sfu()] missing arguments, command ended')
            return

        year = time.localtime()[0]
        term = time.localtime()[1]

        if(term <= 4):
            term = 'spring'
        elif(term >= 5 and term <= 8):
            term = 'summer'
        else:
            term = 'fall'

        # Check if arg needs to be manually split
        if(len(course) == 1):
            # split
            crs = re.findall(r'(\d*\D+)', course[0])
            if(len(crs) < 2):
                crs = re.split(r'(\d+)', course[0])

            if(len(crs) < 2):
                # Bad args
                e_obj = await embed(
                    self.logger,
                    ctx=ctx,
                    title='Bad Arguments',
                    author=ctx.me,
                    colour=WallEColour.ERROR,
                    content=[['Usage', '`.sfu <arg>`'], ['Example', '`.sfu cmpt300`']],
                    footer_text='SFU Error'
                )
                if e_obj is not False:
                    await ctx.send(embed=e_obj, reference=ctx.message)
                self.logger.debug('[SFU sfu()] bad arguments, command ended')
                return

            course_code = crs[0].lower()
            course_num = crs[1].lower()
        else:
            course_code = course[0].lower()
            course_num = course[1].lower()

        url = f'http://www.sfu.ca/bin/wcm/academic-calendar?{year}/{term}/courses/{course_code}/{course_num}'
        self.logger.debug(f'[SFU sfu()] url for get request constructed: {url}')

        async with aiohttp.ClientSession() as req:
            res = await req.get(url)
            data = ''
            if(res.status == 200):
                self.logger.debug('[SFU sfu()] get request successful')
                while True:
                    chunk = await res.content.read(10)
                    if not chunk:
                        break
                    data += str(chunk.decode())
                if data.strip():
                    data = json.loads(data.strip())
            if not data:
                self.logger.debug(f'[SFU sfu()] get resulted in {res.status}')
                e_obj = await embed(
                    self.logger,
                    ctx=ctx,
                    title='Results from SFU',
                    author=ctx.me,
                    colour=WallEColour.ERROR,
                    description=(
                        f'Couldn\'t find anything for:\n{year}/{term.upper()}/{course_code.upper()}'
                        f'/{course_num}/\nMake sure you entered all the arguments '
                        'correctly'
                    ),
                    footer_text='SFU Error'
                )
                if e_obj is not False:
                    await ctx.send(embed=e_obj, reference=ctx.message)
                return

        self.logger.debug('[SFU sfu()] parsing json data returned from get request')

        sfu_url = f'http://www.sfu.ca/students/calendar/{year}/{term}/courses/{course_code}/{course_num}.html'
        link = f'[here]({sfu_url})'
        footer = 'Written by VJ'

        fields = [
            [data['title'], data['description']],
            ["URL", link]
        ]

        embed_obj = await embed(
            self.logger,
            ctx=ctx,
            title='Results from SFU',
            author=ctx.me,
            content=fields,
            colour=WallEColour.ERROR,
            footer_text=footer
        )
        if embed_obj is not False:
            await ctx.send(embed=embed_obj, reference=ctx.message)
        self.logger.debug('[SFU sfu()] out sent to server')

    @commands.command(
        brief="Returns outline details of the specified course",
        help=(
            "Optionally, you may specify term in with the first parameter and/or section with second parameter.\n"
            "Added keyword [next] will look at next semesters outline for [course]; Note [next] will return error if "
            "it is not registration time.\n\n"
            "Arguments:\n"
            "---course: the course to get the outline for\n"
            "---[term|section]\n"
            "------term: the course's term to get the outline for\n"
            "------section: a way to specify a course's specific section\n"
            "---next: will look at the next semester's outline. This will return error if it is not registration time"
            "\n\n"
            "Example:\n"
            "---.outline cmpt300\n"
            "---.outline cmpt300 spring d200\n"
            "---.outline cmpt300 next\n"
            "---.outline cmpt300 summer d200 next\n\n"
        ),
        usage='course [spring|summer|fall] [section] [next]'
    )
    async def outline(self, ctx, *course):
        self.logger.info(
            f'[SFU outline()] outline command detected from user {ctx.message.author} with arguments: {course}'
        )

        usage = [
                ['Usage', '`.outline <course> [<term> <section> next]`\n*<term>, <section>, and next are optional ar'
                    'guments*\nInclude the keyword `next` to look at the next semester\'s outline. Note: `next` is'
                    ' used for course registration purposes and if the next semester info isn\'t available it\'ll '
                    'return an error.'],
                ['Example', '`.outline cmpt300\n .outline cmpt300 fall\n .outline cmpt300 d200\n .outline cmpt300'
                 ' spring d200\n .outline cmpt300 next`']]

        if not course:
            e_obj = await embed(
                self.logger,
                ctx=ctx,
                title='Missing Arguments',
                author=ctx.me,
                colour=WallEColour.ERROR,
                content=usage,
                footer_text='SFU Outline Error'
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj, reference=ctx.message)
            self.logger.debug('[SFU outline()] missing arguments, command ended')
            return
        course = list(course)
        if 'next' in course:
            year = 'registration'
            term = 'registration'
            course.remove('next')
        else:
            year = 'current'
            term = 'current'

        course_code = ''
        course_num = ''
        section = ''

        self.logger.debug('[SFU outline()] parsing args')
        arg_num = len(course)

        if(arg_num > 1 and course[1][:len(course[1]) - 1].isdigit()):
            # User gave course in two parts
            course_code = course[0].lower()
            course_num = course[1].lower()
            course = course[:1] + course[2:]
            arg_num = len(course)
        else:
            # Split course[0] into parts
            crs = re.findall(r'(\d*\D+)', course[0])
            if(len(crs) < 2):
                crs = re.split(r'(\d+)', course[0])  # this incase the course num doesnt end in a letter, need to
                # split with different regex

            if(len(crs) < 2):
                # Bad args
                e_obj = await embed(
                    self.logger,
                    ctx=ctx,
                    title='Bad Arguments',
                    author=ctx.me,
                    colour=WallEColour.ERROR,
                    content=usage,
                    footer_text='SFU Outline Error'
                )
                if e_obj is not False:
                    await ctx.send(embed=e_obj, reference=ctx.message)
                self.logger.debug('[SFU outline()] bad arguments, command ended')
                return

            course_code = crs[0].lower()
            course_num = crs[1]

        # Course and term or section is specified
        if(arg_num == 2):
            # Figure out if section or term was given
            temp = course[1].lower()
            if temp[3].isdigit():
                section = temp
            elif term != 'registration':
                if(temp == 'fall'):
                    term = temp
                elif(temp == 'summer'):
                    term = temp
                elif(temp == 'spring'):
                    term = temp

        # Course, term, and section is specified
        elif(arg_num == 3):
            # Check if last arg is section
            if course[2][3].isdigit():
                section = course[2].lower()
            if term != 'registration':
                if course[1] == 'fall' or course[1] == 'spring' or course[1] == 'summer':
                    term = course[1].lower()
                else:
                    # Send something saying be in this order
                    self.logger.debug('[SFU outline()] args out of order or wrong')
                    e_obj = await embed(
                        self.logger,
                        ctx=ctx,
                        title='Bad Arguments',
                        author=ctx.me,
                        colour=WallEColour.ERROR,
                        description=(
                            'Make sure your arguments are in the following order:\n<course> '
                            '<term> <section>\nexample: `.outline cmpt300 fall d200`\n term and section'
                            ' are optional args'
                        ),
                        footer_text='SFU Outline Error'
                    )
                    if e_obj is not False:
                        await ctx.send(embed=e_obj, reference=ctx.message)
                    return

        # Set up url for get
        if section == '':
            # get req the section
            self.logger.debug('[SFU outline()] getting section')
            res = await self.req.get(
                f'http://www.sfu.ca/bin/wcm/course-outlines?{year}/{term}/{course_code}/{course_num}'
            )
            if(res.status == 200):
                data = ''
                while not res.content.at_eof():
                    chunk = await res.content.readchunk()
                    data += str(chunk[0].decode())
                res = json.loads(data)
                self.logger.debug('[SFU outline()] parsing section data')
                for x in res:
                    if x['sectionCode'] in ['LEC', 'LAB', 'TUT', 'SEM']:
                        section = x['value']
                        break
            else:
                self.logger.debug(f'[SFU outline()] section get resulted in {res.status}')
                e_obj = await embed(
                    self.logger,
                    ctx=ctx,
                    title='SFU Course Outlines',
                    author=ctx.me,
                    colour=WallEColour.ERROR,
                    description=(
                        f'Couldn\'t find anything for `{course_code.upper()} {f"{course_num}".upper()}`\n '
                        'Maybe the course doesn\'t exist? Or isn\'t offered right now.'
                    ),
                    footer_text='SFU Outline Error'
                )
                if e_obj is not False:
                    await ctx.send(embed=e_obj, reference=ctx.message)
                return

        url = f'http://www.sfu.ca/bin/wcm/course-outlines?{year}/{term}/{course_code}/{course_num}/{section}'
        self.logger.debug(f'[SFU outline()] url for get constructed: {url}')

        res = await self.req.get(url)

        if(res.status == 200):
            self.logger.debug('[SFU outline()] get request successful')
            data = ''
            while not res.content.at_eof():
                chunk = await res.content.readchunk()
                data += str(chunk[0].decode())

            data = json.loads(data)
        else:
            self.logger.debug(f'[SFU outline()] full outline get resulted in {res.status}')
            e_obj = await embed(
                self.logger,
                ctx=ctx,
                title='SFU Course Outlines',
                author=ctx.me,
                colour=WallEColour.ERROR,
                description=(
                    f'Couldn\'t find anything for `{course_code.upper()} {f"{course_num}".upper()}`'
                    f'\n Maybe the course doesn\'t exist? Or isn\'t offered right now.'
                ),
                footer_text='SFU Outline Error'
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj, reference=ctx.message)
            return

        self.logger.debug('[SFU outline()] parsing data from get request')
        try:
            # Main course information
            info = data['info']

            # Course schedule information
            schedule = data['courseSchedule']
        except Exception:
            self.logger.debug('[SFU outline()] info keys didn\'t exist')
            e_obj = await embed(
                self.logger,
                ctx=ctx,
                title='SFU Course Outlines',
                author=ctx.me,
                colour=WallEColour.ERROR,
                description=(
                    f'Couldn\'t find anything for `{course_code.upper()} {f"{course_num}".upper()}`\n '
                    f'Maybe the course doesn\'t exist? Or isn\'t offered right now.'),
                footer_text='SFU Outline Error')
            if e_obj is not False:
                await ctx.send(embed=e_obj, reference=ctx.message)
            return

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
            room = f'{x.get("buildingCode", "Room TBD")} {x.get("roomNumber", "")}'
            campus = x['campus']
            crs = f'{crs}{sec_code} {days} {tme}, {room}, {campus}\n'

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
            if(len(details) > 200):
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
            ['Outline', outline],
            ['Title', title],
            ['Instructor', instructor],
            ['Class Times', class_times],
            ['Exam Times', exam_times],
            ['Description', description],
            ['Details', details],
            ['Prerequisites', prerequisites]
        ]

        if corequisites:
            fields.append(['Corequisites', corequisites])
        fields.append(['URL', f'[here]({url})'])
        img = 'http://www.sfu.ca/content/sfu/clf/jcr:content/main_content/image_0.img.1280.high.jpg/1468454298527.jpg'
        e_obj = await embed(
            self.logger,
            ctx=ctx,
            title='SFU Outline Results',
            author=ctx.me,
            colour=WallEColour.ERROR,
            thumbnail=img,
            content=fields,
            footer_text='Written by VJ'
        )
        if e_obj is not False:
            await ctx.send(embed=e_obj, reference=ctx.message)

    @app_commands.command(name="courses", description="Gets all offered courses")
    @app_commands.describe(department="Specify the department to search. Examples: STAT, PHYS, MATH")
    @app_commands.describe(level="Specifies the level of courses to filter for. Examples: 100, 200, 400")
    @app_commands.describe(term="Specify the specific semester to search for. Examples: Spring, Summer, Fall")
    @app_commands.describe(year="Specify the specific year to search for. Examples: 2020, 2024, 2025")
    async def courses(self, interaction: discord.Interaction, department: str = "", level: int = 0,
                  term: str = "registration", year: str = "registration"):
        self.logger.info(
            f'[SFU courses()] courses command detected from user {interaction.user} with arguments: '
            f'department {department}, level {level}, term {term}, year {year}'
        )

        # The default course selection if not specified
        departments = ['CMPT', 'MATH', 'MACM']
        if department:
            departments = [department.upper()]

        if level != 0 and (level < 100 or level >= 1000):
            self.logger.debug(f'[SFU courses()] incorrect level arguments, defaulting to 0')
            level = 0

        courses = []
        for department in departments:
            url = f'http://www.sfu.ca/bin/wcm/course-outlines?{year}/{term}/{department}/'
            self.logger.debug(f'[SFU courses()] url for get constructed: {url}')

            res = await self.req.get(url)
            if res.status == 200:
                self.logger.debug(f'[SFU courses()] get request for {department} successful, parsing data')
                res_json = await res.json()

                # parse data for displaying, sorting, and filtering
                for course in res_json:
                    course['text'] = f"{department}{course['text']}"

                    # we assume all courses have 3 digits
                    if len(course['value']) == 4:
                        course['value'] = course['value'][:3]

                    course['value'] = int(course['value'])
                    if level == 0 or (course['value']//100 == level//100):
                        courses.append(course)
            else:
                self.logger.debug(f'[SFU courses()] get request for {department} resulted in {res.status}')

        if len(departments) > 1:
            courses = sorted(courses, key=lambda k: k['value'])

        self.logger.debug('[SFU courses()] parsing data from get request')
        content_to_embed = []
        number_of_courses_per_page = 20
        number_of_courses = 0
        total_course = 0
        content = ""

        for course in courses:
            course_title = course['title']
            course_number = course['text']
            content += f"\n{course_number} - {course_title}"

            total_course += 1
            number_of_courses += 1
            if total_course > 0 and (number_of_courses % number_of_courses_per_page == 0 or course is courses[-1]):
                number_of_courses = 0
                content_to_embed.append(
                    [["Code - Title", content]]
                )
                content = ""

        title = (f"{', '.join(departments)} {f'{(level//100)*100} level -' if level != 0 else '-'}"
                 f" {f'{term.title()}' if term != 'registration' and term != 'current' else f'{term} term'}"
                 f" {f'{year.title()}' if year != 'registration' and year != 'current' else f'{year} year'}"
                 f"\n(Total Courses: {total_course})\n")

        if len(content_to_embed) == 0:
            self.logger.debug(f'[SFU courses()] resulted in no content')
            e_obj = await embed(
                self.logger, interaction=interaction, title='SFU Courses Error',
                description=(
                    f'Couldn\'t find anything for `department: {", ".join(departments)}'
                    f', level: {level if level != 0 else "all"}, term: {term}, year: {year}`'
                    f'\n Maybe no courses are being offered at that time.'
                ),
                colour=WallEColour.ERROR,
            )
            if e_obj:
                await interaction.response.send_message(embed=e_obj)
                await asyncio.sleep(10)
                await interaction.delete_original_response()
            return
        else:
            await paginate_embed(
                self.logger, bot, content_to_embed=content_to_embed,
                title=title,
                interaction=interaction
            )


    async def cog_unload(self) -> None:
        await self.req.close()
        await super().cog_unload()


async def setup(bot):
    await bot.add_cog(SFU())
