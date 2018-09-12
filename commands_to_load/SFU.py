from discord.ext import commands
import logging
import time
import json # dont need since requests has built in json encoding and decoding
import requests as req
import re
from helper_files.embed import embed 
import helper_files.settings as settings

logger = logging.getLogger('wall_e')

class SFU():
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def sfu(self, ctx, *course):
        logger.info('[SFU sfu()] - sfu command detected from user ' + str(ctx.message.author))

        year = time.localtime()[0]
        term = time.localtime()[1]

        if(term <= 4):
            term = 'spring'
        elif(term >= 5 and term <= 8):
            term = 'summer'
        else:
            term = 'fall'

        #need to check if we need to manually split the arg
        if(len(course) == 1):
            #split
            str = re.findall('(\d*\D+)', course[0])
            if(len(str) < 2):
                str = re.split('(\d+)', course[0])

            courseCode = str[0]
            courseNum = str[1]
        else:
            courseCode = course[0]
            courseNum = course[1]
        
        logger.info('[SFU sfu()] - constructing url for get request')
        sfuUrl='http://www.sfu.ca/students/calendar/%s/%s/courses/%s/%s.html' % (year, term, courseCode, courseNum)
        #grab the things
        url = 'http://www.sfu.ca/bin/wcm/academic-calendar?%s/%s/courses/%s/%s' % (year, term, courseCode, courseNum)
        
        logger.info('[SFU sfu()] - get request made')
        res = req.get(url)
        if(res.status_code != 404):
            logger.info('[SFU sfu()] - get request successful')
            data = res.json()
        else:
            logger.error('[SFU sfu()] - get resulted in 404. Notifying user of 404')
            eObj = embed(title='Results from SFU', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, colour=0xA6192E, description='Couldn\'t find anything for:\n%s/%s/%s/%s/\nMake sure you entered all the arguments correctly' % (year.upper(), term.upper(), courseCode.upper(), courseNum.upper()))
            await ctx.sent(embed=eObj)
            return

        logger.info('[SFU sfu()] - constructing embed with information about ' + str(courseCode) + str(courseNum))
        title='Results from SFU'
        colour=0xA6192E
        link='[here](%s)' % sfuUrl
        # TODO: thumbnail
        footer='Written by VJ'

        fields = [
            [data['title'], data['description']], 
            ["URL", link]
        ]
        
        embedObj = embed(title=title, author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, content=fields, colour=colour, footer=footer)
        await ctx.send(embed=embedObj)
        logger.info('[SFU sfu()] - output send to server')

    @commands.command()
    async def outline(self, ctx, *course):
        logger.info('[SFU outline()] - outline command detected from user ' + str(ctx.message.author))        
        year = time.localtime()[0]
        term = time.localtime()[1]

        courseCode = ''
        courseNum = ''
        section = 'd100' # this is the default section
        
        if(term <= 4):
            term = 'spring'
        elif(term >= 5 and term <= 8):
            term = 'summer'
        else:
            term = 'fall'
        
        logger.info('[SFU outline()] - parsing args')
        argNum = len(course)
        # course and term or section is specified
        if(argNum == 2):
            # figure out if section or term was given
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

        # course, term, and section is specified
        elif(argNum == 3):
            # check if last arg is the section
            # so check for len == 3
            if(len(course[2]) == 4 and course[1] == 'fall' or course[1] == 'spring' or course[1] == 'summer'):
                term = course[1].lower()
                section = course[2].lower()
            else:
                # send something saying be in this order
                logger.error('[SFU outline()] - args out of order or just wrong')
                eObj = embed(title='SFU Course Outlines', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, colour=0xA6192E, description='Make sure you arg\'s are in the following order:\n<course> <term> <section>\nexample: .outline cmpt300 fall d200')
                await ctx.send(embed=eObj)
                return
        
        # split course[0] into the parts
        crs = re.findall('(\d*\D+)', course[0])
        if(len(crs) < 2):
            crs = re.split('(\d+)', course[0]) # this incase the course num doesnt end in a letter, need to split with different regex

        courseCode = crs[0]
        courseNum = crs[1]

        # set up url for get
        logger.info('[SFU outline()] - constructing url for get request')
        url = 'http://www.sfu.ca/bin/wcm/course-outlines?%s/%s/%s/%s/%s' % (year, term, courseCode, courseNum, section)
        logger.info('[SFU outline()] - url for get request constructed')

        # make get request and get json data
        logger.info('[SFU outline()] - get request made')
        res = req.get(url)
        if(res.status_code != 404):
            logger.info('[SFU outline()] - get request successful')
            data = res.json()
        else:
            logger.error('[SFU outline()] - get resulted in 404. Notifying user of 404')
            eObj = embed(title='SFU Course Outlines', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, colour=0xA6192E, description='Couldn\'t find anything for:\n%s/%s/%s/%s/%s\nMake sure you entered all the arguments correctly' % (year.upper(), term.upper(), courseCode.upper(), courseNum.upper(), section.upper()))
            await ctx.sent(embed=eObj)
            return
        
        # Parse data into pieces
        logger.info('[SFU outline()] - parsing data from get request')
        outline = data['info']['outlinePath'].upper()
        title = data['info']['title']
        instructor = data['instructor'][0]['name'] + '\n(' + data['instructor'][0]['email'] + ')'
        
        # Course schedule info
        schedule = data['courseSchedule']
        course = ''
        for x in schedule:
            # [LEC] days time, room, campus
            secCode = '[' + x['sectionCode'] + ']'
            days = x['days']
            tme = x['startTime'] + '-' + x['endTime']
            room = x['buildingCode'] + ' ' + x['roomNumber']
            campus = x['campus']
            course = course + secCode + ' ' + days + ' ' + tme + ', ' + room + ', ' + campus + '\n'

        classTimes = course

        # Exam info
        tim = data['examSchedule'][0]['startTime'] + '-' + data['examSchedule'][0]['endTime']
        date = data['examSchedule'][0]['startDate'].split()
        date = date[0] + ' ' + date[1] + ' ' + date[2]
        roomInfo = ''

        try:
            # see if room info is available
            roomInfo = data['examSchedule'][0]['buildingCode'] + ' ' + data['schedule']['roomNumber'] + ', ' + data['examSchedule'][0]['campus']
        except KeyError:
            pass

        if(not roomInfo):
            examTimes = tim + ' ' + date
        else:
            examTimes = tim + ' ' + date + '\n' + roomInfo

        # Other details
        # need to cap len for details
        description = data['info']['description']
        details = data['info']['courseDetails'][:200] + '\n(...)'
        prerequisites  = data['info']['prerequisites']

        url = 'http://www.sfu.ca/outlines.html?%s/%s/%s/%s/%s' % (year, term, courseCode, courseNum, section)
        
        logger.info('[SFU outline()] - building embed object with outline info of ' + str(courseCode) + str(courseNum))
        # make tuple of the data for the fields
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
        # get embed object 
        eObj = embed(title='SFU Outline Results', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, colour=0xA6192E, content=fields, footer='Written by VJ')
        # send embed object
        await ctx.send(embed=eObj)

def setup(bot):
    bot.add_cog(SFU(bot))