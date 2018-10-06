from discord.ext import commands
import logging
import time
import json # dont need since requests has built in json encoding and decoding
import requests as req
import re
from helper_files.embed import embed 
import helper_files.settings as settings
import html

logger = logging.getLogger('wall_e')
sfuRed = 0xA6192E

class SFU():
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def sfu(self, ctx, *course):
        logger.info('[SFU sfu()] sfu command detected from user ' + str(ctx.message.author))

        if(not course):
            eObj = embed(title='Missing Arguments', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, colour=sfuRed, content=[['Usage', '`.sfu <arg>`'],['Example', '`.sfu cmpt300`']], footer='SFU Error')
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
            #split
            crs = re.findall('(\d*\D+)', course[0])
            if(len(crs) < 2):
                crs = re.split('(\d+)', course[0])

            if(len(crs) < 2):
                # Bad args
                eObj = embed(title='Bad Arguments', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, colour=sfuRed, content=[['Usage', '`.sfu <arg>`'],['Example', '`.sfu cmpt300`']], footer='SFU Error')
                await ctx.send(embed=eObj)
                logger.info('[SFU outline()] bad arguments, command ended')
                return
            
            courseCode = crs[0]
            courseNum = crs[1]
        else:
            courseCode = course[0]
            courseNum = course[1]

        url = 'http://www.sfu.ca/bin/wcm/academic-calendar?%s/%s/courses/%s/%s' % (year, term, courseCode, courseNum)
        logger.info('[SFU sfu()] url for get request constructed: %s' % url)

        res = req.get(url)
        if(res.status_code != 404):
            logger.info('[SFU sfu()] get request successful')
            data = res.json()
        else:
            logger.info('[SFU sfu()] get resulted in 404')
            eObj = embed(title='Results from SFU', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, colour=sfuRed, description='Couldn\'t find anything for:\n%s/%s/%s/%s/\nMake sure you entered all the arguments correctly' % (year, term.upper(), courseCode.upper(), courseNum), footer='SFU Error')
            await ctx.send(embed=eObj)
            return
        
        logger.info('[SFU sfu()] parsing json data returned from get request')
        title = 'Results from SFU'
        colour = sfuRed

        sfuUrl='http://www.sfu.ca/students/calendar/%s/%s/courses/%s/%s.html' % (year, term, courseCode, courseNum)
        link = '[here](%s)' % sfuUrl
        footer = 'Written by VJ'

        fields = [
            [data['title'], data['description']], 
            ["URL", link]
        ]

        embedObj = embed(title='Results from SFU', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, content=fields, colour=colour, footer=footer)
        await ctx.send(embed=embedObj)
        logger.info('[SFU sfu()] out sent to server')        

    @commands.command()
    async def outline(self, ctx, *course):
        logger.info('[SFU outline()] outline command detected from user ' + str(ctx.message.author))
        
        usage = [
                ['Usage', '`.outline <course> [<term> <section>]`\n*<term> and <section> are optional arguments*'], 
                ['Example', '`.outline cmpt300 fall d200`']
            ]

        if(not course):
            eObj = embed(title='Missing Arguments', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, colour=sfuRed, content=usage, footer='SFU Outline Error')
            await ctx.send(embed=eObj)
            logger.info('[SFU outline()] missing arguments, command ended')
            return

        year = 'current'
        term = 'registration'

        courseCode = ''
        courseNum = ''
        section = 'd100'
        
        logger.info('[SFU outline()] parsing args')
        argNum = len(course)

        if(argNum > 1 and course[1][:len(course[1])-1].isdigit()):
            # User gave course in two parts
            courseCode = course[0].lower()
            courseNum = course[1].lower()
            course = course[:1] + course[2:]
            argNum = len(course)
        else:
            # Split course[0] into parts
            crs = re.findall('(\d*\D+)', course[0])
            if(len(crs) < 2):
                crs = re.split('(\d+)', course[0]) # this incase the course num doesnt end in a letter, need to split with different regex

            if(len(crs) < 2):
                # Bad args
                eObj = embed(title='Bad Arguments', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, colour=sfuRed, content=usage, footer='SFU Outline Error')
                await ctx.send(embed=eObj)
                logger.info('[SFU outline()] bad arguments, command ended')
                return

            courseCode = crs[0]
            courseNum = crs[1]

        # Course and term or section is specified
        if(argNum == 2):
            # Figure out if section or term was given
            temp = course[1].lower()

            if(len(temp) == 4):
                if(temp != 'fall'):
                    section = temp
                else:
                    term = temp
            elif(temp == 'summer'):
                term = temp
            elif(temp == 'spring'):
                term = temp
        
        # Course, term, and section is specified
        elif(argNum == 3):
            # Check iff last arg is section
            if(len(course[2]) == 4 and (course[1] == 'fall' or course[1] == 'spring' or course[1] == 'summer')):
                term = course[1].lower()
                section = course[2].lower()
            else:
                # Send something saying be in this order
                logger.error('[SFU outline] args out of order or wrong')
                eObj = embed(title='Bad Arguments', author=settings.BOT_NAME, avatar=settings.BOT_NAME, colour=sfuRed, description='Make sure your arguments are in the following order:\n<course> <term> <section>\nexample: `.outline cmpt300 fall d200`\n term and section are optional args', footer='SFU Outline Error')
                await ctx.send(embed=eObj)
                return

        # Set up url for get
        url = 'http://www.sfu.ca/bin/wcm/course-outlines?%s/%s/%s/%s/%s' % (year, term, courseCode, courseNum, section)
        logger.info('[SFU outline()] url for get constructed: ' + url)

        res = req.get(url)
        if(res.status_code != 404):
            logger.info('[SFU outline()] get request successful')
            data = res.json()
        else:
            logger.error('[SFU outline()] get resulted in 404')
            eObj = embed(title='SFU Course Outlines', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, colour=sfuRed, description='Couldn\'t find anything for:\n`' + courseCode + ' ' + courseNum + '`', footer='SFU Outline Error')
            await ctx.send(embed=eObj)
            return

        logger.info('[SFU outline()] parsing data from get request')
        outline = data['info']['outlinePath'].upper()
        title = data['info']['title']
        instructor = data['instructor'][0]['name'] + '\n[' + data['instructor'][0]['email'] + ']'
        
        # Course schedule info
        schedule = data['courseSchedule']
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
        examTimes = 'N/A'
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
            roomInfo = data['examSchedule'][0]['buildingCode'] + ' ' + data['schedule']['roomNumber'] + ', ' + data['examSchedule'][0]['campus']
            examTimes += '\n' + roomInfo
        except Exception:
            pass
        
        # Other details
        # need to cap len for details
        description = data['info']['description']
        details = html.unescape(data['info']['courseDetails'])
        details = re.sub('<[^<]+?>', '', details)
        if(len(details) > 200):
            details = details[:200] + '\n(...)'
        
        prerequisites  = data['info']['prerequisites'] or "None"

        url = 'http://www.sfu.ca/outlines.html?%s' % data['info']['outlinePath']
        
        logger.info('[SFU outline()] finished parsing data for: %s' % data['info']['outlinePath'])
        
        # Make tuple of the data for the fields
        fields = [
            ['Outline', outline], 
            ['Title', title], 
            ['Instructor', instructor], 
            ['Class Times', classTimes], 
            ['Exam Times', examTimes], 
            ['Description', description], 
            ['Details', details], 
            ['Prerequisites', prerequisites], 
            ['URL', '[here](%s)' % url]
        ]
        img = 'http://www.sfu.ca/content/sfu/clf/jcr:content/main_content/image_0.img.1280.high.jpg/1468454298527.jpg'

        eObj = embed(title='SFU Outline Results', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, colour=sfuRed, thumbnail=img, content=fields, footer='Written by VJ')
        await ctx.send(embed=eObj)

def setup(bot):
    bot.add_cog(SFU(bot))