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

        
def setup(bot):
    bot.add_cog(SFU(bot))