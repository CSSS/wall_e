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
        logger.info('[SFU sfu()] sfu command detected from user ' + str(ctx.message.author))

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

            courseCode = crs[0]
            courseNum = crs[1]
        else:
            courseCode = course[0]
            courseNum = course[1]

        url = 'http://www.sfu.ca/bin/wcm/academic-calendar?%s/%s/courses/%s/%s' % (year, term, courseCode, courseNum)
        logger.info('[SFU sfu()] url for get request constructed: %s' url)

        res = req.get(url)
        if(res.status_code != 404):
            logger.info('[SFU sfu()] get request successful')
            data = res.json()
        else:
            logger.info('[SFU sfu()] get resulted in 404')
            eObj = embed(title='Results from SFU', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, colour=0xA6192E, description='Couldn\'t find anything for:\n%s/%s/%s/%s/\nMake sure you entered all the arguments correctly' % (year, term.upper(), courseCode.upper(), courseNum))
            await ctx.send(embed=eObj)
            return
        
        logger.info('[SFU sfu()] parsing json data returned from get request')
        title = 'Results from SFU'
        colour = 0xA6192E

        sfuUrl='http://www.sfu.ca/students/calendar/%s/%s/courses/%s/%s.html' % (year, term, courseCode, courseNum)
        link = '[here](%s)' % sfuUrl
        footer = 'Written by VJ'

        fields = [
            [data['title'], data['description'], 
            ["URL", link]
        ]

def setup(bot):
    bot.add_cog(SFU(bot))