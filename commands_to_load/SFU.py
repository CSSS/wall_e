from discord.ext import commands
import logging
import time
import json # dont need since requests has built in json encoding and decoding
import requests as req
logger = logging.getLogger('wall_e')

class sfu():
    def __init__(self, bot):
        self.bot = bot
        global BOT_NAME = bot.user.name
        global BOT_Avatar = bot.user.avatar
    
    @commands.command()
    async def sfu(self, ctx, *course):
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
        
        sfuUrl='http://www.sfu.ca/students/calendar/%s/%s/courses/%s/%s.html' % (year, term, courseCode, courseNum)
        #grab the things
        url = 'http://www.sfu.ca/bin/wcm/academic-calendar?%s/%s/courses/%s/%s' % (year, term, courseCode, courseNum)
        
        res = req.get(url)
        if(res.status_code != 404):
            data = res.json()
        else:
            eObj = embed(title='Results from SFU', author=BOT_NAME, avatar=BOT_AVATAR, colour=0xA6192E, description='Couldn\'t find anything for:\n%s/%s/%s/%s/\nMake sure you entered all the arguments correctly' % (year.upper(), term.upper(), courseCode.upper(), courseNum.upper()))
            await ctx.sent(embed=eObj)
            return

        
        title='Results from SFU'
        colour=0xA6192E
        link='[here](%s)' % sfuUrl
        #thumbnail <do later>
        footer='Written by VJ'

        fields = [
            [data['title'], data['description']], 
            ["URL", link]
        ]
        
        embedObj = embed(title=title, author=BOT_NAME, avatar=BOT_AVATAR, content=fields, colour=colour, footer=footer)
        await ctx.send(embed=embedObj)

    @commands.command()
    async def outline(self, ctx, *course):
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
                eObj = embed(title='SFU Course Outlines', author=BOT_NAME, avatar=BOT_AVATAR, colour=0xA6192E, description='Make sure you arg\'s are in the following order:\n<course> <term> <section>\nexample: .outline cmpt300 fall d200')
                await ctx.send(embed=eObj)
                return
        
        # split course[0] into the parts
        crs = re.findall('(\d*\D+)', course[0])
        if(len(crs) < 2):
            crs = re.split('(\d+)', course[0]) # this incase the course num doesnt end in a letter, need to split with different regex

        courseCode = crs[0]
        courseNum = crs[1]

        # set up url for get
        url = 'http://www.sfu.ca/bin/wcm/course-outlines?%s/%s/%s/%s/%s' % (year, term, courseCode, courseNum, section)
        
        # make get request and get json data
        res = req.get(url)
        if(res.status_code != 404):
            data = res.json()
        else:
            eObj = embed(title='SFU Course Outlines', author=BOT_NAME, avatar=BOT_AVATAR, colour=0xA6192E, description='Couldn\'t find anything for:\n%s/%s/%s/%s/%s\nMake sure you entered all the arguments correctly' % (year.upper(), term.upper(), courseCode.upper(), courseNum.upper(), section.upper()))
            await ctx.sent(embed=eObj)
            return
        
        # Parse data into pieces
        
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
        eObj = embed(title='SFU Outline Results', author=BOT_NAME, avatar=BOT_AVATAR, colour=0xA6192E, content=fields, footer='Written by VJ')
        # send embed object
        await ctx.send(embed=eObj)