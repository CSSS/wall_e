from discord.ext import commands
import logging
import time
import json  # dont need since requests has built in json encoding and decoding
import re
from helper_files.embed import embed
import helper_files.settings as settings
import html
import aiohttp

logger = logging.getLogger('wall_e')
sfuRed = 0xA6192E


class SFU():
    def __init__(self, bot):
        self.bot = bot
        self.req = aiohttp.ClientSession(loop=bot.loop)

    @commands.command()
    async def sfu(self, ctx, *course):
        logger.info('[SFU sfu()] sfu command detected from user ' + str(ctx.message.author))
        logger.info('[SFU sfu()] arguments given: ' + str(course))

        if(not course):
            eObj = await embed(ctx, title='Missing Arguments', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR,
                               colour=sfuRed, content=[['Usage', '`.sfu <arg>`'], ['Example', '`.sfu cmpt300`']],
                               footer='SFU Error')
            if eObj is not False:
                await ctx.send(embed=eObj)
            logger.info('[SFU sfu()] missing arguments, command ended')
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
                eObj = await embed(ctx, title='Bad Arguments', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR,
                                   colour=sfuRed, content=[['Usage', '`.sfu <arg>`'], ['Example', '`.sfu cmpt300`']],
                                   footer='SFU Error')
                if eObj is not False:
                    await ctx.send(embed=eObj)
                logger.info('[SFU sfu()] bad arguments, command ended')
                return

            courseCode = crs[0].lower()
            courseNum = crs[1].lower()
        else:
            courseCode = course[0].lower()
            courseNum = course[1].lower()

        url = 'http://www.sfu.ca/bin/wcm/academic-calendar?{0}/{1}/courses/{2}/{3}'.format(year, term, courseCode,
                                                                                           courseNum)
        logger.info('[SFU sfu()] url for get request constructed: {}'.format(url))

        async with aiohttp.ClientSession() as req:
            res = await req.get(url)

            if(res.status == 200):
                logger.info('[SFU sfu()] get request successful')
                data = ''
                while True:
                    chunk = await res.content.read(10)
                    if not chunk:
                        break
                    data += str(chunk.decode())
                data = json.loads(data)
            else:
                logger.info('[SFU sfu()] get resulted in ' + str(res.status))
                eObj = await embed(ctx, title='Results from SFU', author=settings.BOT_NAME,
                                   avatar=settings.BOT_AVATAR, colour=sfuRed, description='Couldn\'t find anything f'
                                   + 'or:\n{0}/{1}/{2}/{3}/\nMake sure you entered all the arguments '
                                   + 'correctly'.format(year, term.upper(), courseCode.upper(), courseNum),
                                   footer='SFU Error')
                if eObj is not False:
                    await ctx.send(embed=eObj)
                return

        logger.info('[SFU sfu()] parsing json data returned from get request')

        sfuUrl = 'http://www.sfu.ca/students/calendar/{0}/{1}/courses/{2}/{3}.html'.format(year, term, courseCode,
                                                                                           courseNum)
        link = '[here]({})'.format(sfuUrl)
        footer = 'Written by VJ'

        fields = [
            [data['title'], data['description']],
            ["URL", link]
        ]

        embedObj = await embed(ctx, title='Results from SFU', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR,
                               content=fields, colour=sfuRed, footer=footer)
        if embedObj is not False:
            await ctx.send(embed=embedObj)
        logger.info('[SFU sfu()] out sent to server')

    @commands.command()
    async def outline(self, ctx, *course):
        logger.info('[SFU outline()] outline command detected from user ' + str(ctx.message.author))
        logger.info('[SFU outline()] arguments given: ' + str(course))

        usage = [
                ['Usage', '`.outline <course> [<term> <section> next]`\n*<term>, <section>, and next are optional ar'
                    + 'guments*\nInclude the keyword `next` to look at the next semester\'s outline. Note: `next` is'
                    + ' used for course registration purposes and if the next semester info isn\'t available it\'ll '
                    + 'return an error.'],
                ['Example', '`.outline cmpt300\n .outline cmpt300 fall\n .outline cmpt300 d200\n .outline cmpt300'
                 + ' spring d200\n .outline cmpt300 next`']]

        if(not course):
            eObj = await embed(ctx, title='Missing Arguments', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR,
                               colour=sfuRed, content=usage, footer='SFU Outline Error')
            if eObj is not False:
                await ctx.send(embed=eObj)
            logger.info('[SFU outline()] missing arguments, command ended')
            return
        course = list(course)
        if 'next' in course:
            year = 'registration'
            term = 'registration'
            course.remove('next')
        else:
            year = 'current'
            term = 'current'

        courseCode = ''
        courseNum = ''
        section = ''

        logger.info('[SFU outline()] parsing args')
        argNum = len(course)

        if(argNum > 1 and course[1][:len(course[1]) - 1].isdigit()):
            # User gave course in two parts
            courseCode = course[0].lower()
            courseNum = course[1].lower()
            course = course[:1] + course[2:]
            argNum = len(course)
        else:
            # Split course[0] into parts
            crs = re.findall(r'(\d*\D+)', course[0])
            if(len(crs) < 2):
                crs = re.split(r'(\d+)', course[0])  # this incase the course num doesnt end in a letter, need to
                # split with different regex

            if(len(crs) < 2):
                # Bad args
                eObj = await embed(ctx, title='Bad Arguments', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR,
                                   colour=sfuRed, content=usage, footer='SFU Outline Error')
                if eObj is not False:
                    await ctx.send(embed=eObj)
                logger.info('[SFU outline()] bad arguments, command ended')
                return

            courseCode = crs[0].lower()
            courseNum = crs[1]

        # Course and term or section is specified
        if(argNum == 2):
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
        elif(argNum == 3):
            # Check if last arg is section
            if course[2][3].isdigit():
                section = course[2].lower()
            if term != 'registration':
                if course[1] == 'fall' or course[1] == 'spring' or course[1] == 'summer':
                    term = course[1].lower()
                else:
                    # Send something saying be in this order
                    logger.info('[SFU outline] args out of order or wrong')
                    eObj = await embed(ctx, title='Bad Arguments', author=settings.BOT_NAME,
                                       avatar=settings.BOT_AVATAR, colour=sfuRed,
                                       description='Make sure your arguments are in the following order:\n<course> '
                                       + '<term> <section>\nexample: `.outline cmpt300 fall d200`\n term and section'
                                       + ' are optional args', footer='SFU Outline Error')
                    if eObj is not False:
                        await ctx.send(embed=eObj)
                    return

        # Set up url for get
        if section == '':
            # get req the section
            logger.info('[SFU outline()] getting section')
            res = await self.req.get('http://www.sfu.ca/bin/wcm/course-outlines?{0}/{1}/{2}/{3}'.format(year, term,
                                                                                                        courseCode,
                                                                                                        courseNum))
            if(res.status == 200):
                data = ''
                while not res.content.at_eof():
                    chunk = await res.content.readchunk()
                    data += str(chunk[0].decode())
                res = json.loads(data)
                logger.info('[SFU outline()] parsing section data')
                for x in res:
                    if x['sectionCode'] in ['LEC', 'LAB', 'TUT', 'SEM']:
                        section = x['value']
                        break
            else:
                logger.info('[SFU outline()] section get resulted in ' + str(res.status))
                eObj = await embed(ctx, title='SFU Course Outlines', author=settings.BOT_NAME,
                                   avatar=settings.BOT_AVATAR, colour=sfuRed, description='Couldn\'t find anything '
                                   + 'for `' + courseCode.upper() + ' ' + str(courseNum).upper() + '`\n Maybe the '
                                   + 'course doesn\'t exist? Or isn\'t offerend right now.', footer='SFU Outline '
                                   + 'Error')
                if eObj is not False:
                    await ctx.send(embed=eObj)
                return

        url = 'http://www.sfu.ca/bin/wcm/course-outlines?{0}/{1}/{2}/{3}/{4}'.format(year, term, courseCode,
                                                                                     courseNum, section)
        logger.info('[SFU outline()] url for get constructed: ' + url)

        res = await self.req.get(url)

        if(res.status == 200):
            logger.info('[SFU outline()] get request successful')
            data = ''
            while not res.content.at_eof():
                chunk = await res.content.readchunk()
                data += str(chunk[0].decode())

            data = json.loads(data)
        else:
            logger.info('[SFU outline()] full outline get resulted in ' + str(res.status))
            eObj = await embed(ctx, title='SFU Course Outlines', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR,
                               colour=sfuRed, description='Couldn\'t find anything for `' + courseCode.upper() + ' '
                               + str(courseNum).upper() + '`\n Maybe the course doesn\'t exist? Or isn\'t offerend '
                               + 'right now.', footer='SFU Outline Error')
            if eObj is not False:
                await ctx.send(embed=eObj)
            return

        logger.info('[SFU outline()] parsing data from get request')
        try:
            # Main course information
            info = data['info']

            # Course schedule information
            schedule = data['courseSchedule']
        except Exception:
            logger.info('[SFU outline()] info keys didn\'t exist')
            eObj = await embed(ctx, title='SFU Course Outlines', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR,
                               colour=sfuRed, description='Couldn\'t find anything for `' + courseCode.upper() + ' '
                               + str(courseNum).upper() + '`\n Maybe the course doesn\'t exist? Or isn\'t offerend '
                               + 'right now.', footer='SFU Outline Error')
            if eObj is not False:
                await ctx.send(embed=eObj)
            return

        outline = info['outlinePath'].upper()
        title = info['title']
        try:
            # instructor = data['instructor'][0]['name'] + '\n[' + data['instructor'][0]['email'] + ']'
            instructor = ''
            instructors = data['instructor']
            for prof in instructors:
                instructor += prof['name']
                instructor += ' [{}]\n'.format(prof['email'])
        except Exception:
            instructor = 'TBA'

        # Course schedule info parsing
        crs = ''
        for x in schedule:
            # [LEC] days time, room, campus
            secCode = '[' + x['sectionCode'] + ']'
            days = x['days']
            tme = x['startTime'] + '-' + x['endTime']
            room = x['buildingCode'] + ' ' + x['roomNumber']
            campus = x['campus']
            crs = crs + secCode + ' ' + days + ' ' + tme + ', ' + room + ', ' + campus + '\n'

        classTimes = crs

        # Exam info
        examTimes = 'TBA'
        roomInfo = ''
        tim = ''
        date = ''
        try:
            # Course might not have an exam
            tim = data['examSchedule'][0]['startTime'] + '-' + data['examSchedule'][0]['endTime']
            date = data['examSchedule'][0]['startDate'].split()
            date = date[0] + ' ' + date[1] + ' ' + date[2]

            examTimes = tim + ' ' + date

            # Room info much later
            roomInfo = data['examSchedule'][0]['buildingCode'] + ' ' + data['schedule']['roomNumber'] + ', '
            + data['examSchedule'][0]['campus']
            examTimes += '\n' + roomInfo
        except Exception:
            pass
        # Other details
        # need to cap len for details
        description = data['info']['description']
        try:
            details = html.unescape(data['info']['courseDetails'])
            details = re.sub('<[^<]+?>', '', details)
            if(len(details) > 200):
                details = details[:200] + '\n(...)'
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

        url = 'http://www.sfu.ca/outlines.html?{}'.format(data['info']['outlinePath'])
        logger.info('[SFU outline()] finished parsing data for: {}'.format(data['info']['outlinePath']))
        # Make tuple of the data for the fields
        fields = [
            ['Outline', outline],
            ['Title', title],
            ['Instructor', instructor],
            ['Class Times', classTimes],
            ['Exam Times', examTimes],
            ['Description', description],
            ['Details', details],
            ['Prerequisites', prerequisites]
        ]

        if corequisites:
            fields.append(['Corequisites', corequisites])
        fields.append(['URL', '[here]({})'.format(url)])
        img = 'http://www.sfu.ca/content/sfu/clf/jcr:content/main_content/image_0.img.1280.high.jpg/1468454298527.jpg'
        eObj = await embed(ctx, title='SFU Outline Results', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR,
                           colour=sfuRed, thumbnail=img, content=fields, footer='Written by VJ')
        if eObj is not False:
            await ctx.send(embed=eObj)

    def __del__(self):
        self.req.close()


def setup(bot):
    bot.add_cog(SFU(bot))
