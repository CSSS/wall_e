from discord.ext import commands
import logging
import redis
logger = logging.getLogger('wall_e')

class Misc():

    def __init__(self, bot):
        self.bot = bot
    
        #setting up database connection
        try:
            self.bot.loop.create_task(get_messages())
            self.r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
            message_subscriber = self.r.pubsub(ignore_subscribe_messages=True)
            message_subscriber.subscribe('__keyevent@0__:expired')
            logger.info("[Misc __init__] redis connection established")
        except Exception as e:
            logger.error("[Misc __init__] enountered following exception when setting up redis connection\n{}".format(e))


#######################
## NEEDS DESCRIPTION ##
#######################
async def get_messages(self):
    await self.bot.wait_until_ready()
    while True:
        message = message_subscriber.get_message()
        if message is not None and message['type'] == 'message':
            try:
                cid_mid_dct = json.loads(message['data'])
                chan = self.bot.get_channel(cid_mid_dct['cid'])
                msg = await chan.get_message(cid_mid_dct['mid'])
                ctx = await self.bot.get_context(msg)
                if ctx.valid:
                    fmt = '<@{0}> ```{1}```'
                    await ctx.send(fmt.format(ctx.message.author.id, ctx.message.content))
            except Exception as error:
                logger.error('[main.py get_message()] Ignoring exception when generating reminder:')
                traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        await asyncio.sleep(2)

    @commands.command()
    async def poll(self, ctx, *questions):
        logger.info("[Misc poll()] poll command detected")
        if len(questions) > 12:
            logger.error("[Misc poll()] was called with too many options.")
            await ctx.send("Poll Error:\n```Please only submit a maximum of 11 options for a multi-option question.```")
            return
        elif len(questions) == 1:
            logger.info("[Misc poll()] yes/no poll being constructed.")
            post = await ctx.send("Poll:\n" + "```" + questions[0] + "```")
            await post.add_reaction(u"\U0001F44D")
            await post.add_reaction(u"\U0001F44E")
            logger.info("[Misc poll()] yes/no poll constructed and sent to server.")
            return
        if len(questions) == 2:
            logger.error("[Misc poll()] poll with only 2 arguments detected.")
            await ctx.send("Poll Error:\n```Please submit at least 2 options for a multi-option question.```")
            return
        elif len(questions) == 0:
            logger.error("[Misc poll()] poll with no arguments detected.")
            await ctx.send('```Usage: .poll <Question> [Option A] [Option B] ...```')
            return
        else:
            logger.info("[Misc poll()] multi-option poll being constructed.")
            questions = list(questions)
            optionString = "\n"
            numbersEmoji = [":zero:", ":one:", ":two:", ":three:", ":four:", ":five:", ":six:", ":seven:", ":eight:", ":nine:", ":keycap_ten:"]
            numbersUnicode = [u"0\u20e3", u"1\u20e3", u"2\u20e3", u"3\u20e3", u"4\u20e3", u"5\u20e3", u"6\u20e3", u"7\u20e3", u"8\u20e3", u"9\u20e3", u"\U0001F51F"]
            question = questions.pop(0)
            options = 0
            for m, n in zip(numbersEmoji, questions):
                optionString += m + ": " + n +"\n"
                options += 1
            pollPost = await ctx.send("Poll:\n```" + question + "```" + optionString)
            logger.info("[Misc poll()] multi-option poll message contructed and sent.")
            for i in range(0, options):
                await pollPost.add_reaction(numbersUnicode[i])
            logger.info("[Misc poll()] reactions added to multi-option poll message.")


    @commands.command()
    async def remindme(self, ctx, timeUntil, message):
        logger.info("[Misc remindme()] remindme command detected")
        time_struct, parse_status = parsedatetime.Calendar().parse(timeUntil)
        if parse_status == 0:
            logger.info("[Misc remindme()] couldn't parse the time")
            await ctx.send('```Could not parse time!```')
            return
        expire_seconds = int(mktime(time_struct) - time.time())
        json_string = json.dumps({'cid': ctx.channel.id, 'mid': ctx.message.id})
        self.r.set(json_string, '', expire_seconds)
        fmt = '```Reminder set for {0} seconds from now```'
        await ctx.send(fmt.format(expire_seconds))
        logger.info("[Misc remindme()] reminder has been contructed and sent.")


def setup(bot):
    bot.add_cog(Misc(bot))
