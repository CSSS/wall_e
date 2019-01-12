import discord
from discord.ext import commands
import json
import logging
import redis
import asyncio
import parsedatetime
import time
from time import mktime
import helper_files.testenv
import traceback
import sys
import helper_files.settings as settings
from helper_files.embed import embed
import os

logger = logging.getLogger('wall_e')

class Reminders():

	def __init__(self, bot):
		self.bot = bot

		#setting up database connection
		try:
			self.r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
			self.message_subscriber = self.r.pubsub(ignore_subscribe_messages=True)
			self.message_subscriber.subscribe('__keyevent@0__:expired')
			self.bot.loop.create_task(self.get_messages())
			logger.info("[Reminders __init__] redis connection established")
		except Exception as e:
			logger.error("[Reminders __init__] enountered following exception when setting up redis connection\n{}".format(e))

	@commands.command()
	async def remindmein(self, ctx, *args):
		logger.info("[Reminders remindme()] remindme command detected from user "+str(ctx.message.author))
		parsedTime=''
		message=''
		parseTime=True
		for index, value in enumerate(args):
			if parseTime == True:
				if value == 'to':
					parseTime = False
				else:
					parsedTime+=str(value)+" "
			else:
				message+=str(value)+" "
		how_to_call_command="\nPlease call command like so:\nremindmein <time|minutes|hours|days> to <what to remind you about>\nExample: \".remindmein 10 minutes to turn in my assignment\""
		if parsedTime == '':
			logger.info("[Reminders remindme()] was unable to extract a time")
			eObj = embed(title='RemindMeIn Error', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="unable to extract a time"+str(how_to_call_command))
			await ctx.send(embed=eObj)
			return
		if message == '':
			logger.info("[Reminders remindme()] was unable to extract a message")
			eObj = embed(title='RemindMeIn Error', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="unable to extract a string"+str(how_to_call_command))
			await ctx.send(embed=eObj)
			return
		timeUntil = str(parsedTime)
		logger.info("[Reminders remindme()] extracted time is "+str(timeUntil))
		logger.info("[Reminders remindme()] extracted message is "+str(message))
		time_struct, parse_status = parsedatetime.Calendar().parse(timeUntil)
		if parse_status == 0:
			logger.info("[Reminders remindme()] couldn't parse the time")
			eObj = embed(title='RemindMeIn Error', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="Could not parse time!"+how_to_call_command)
			await ctx.send(embed=eObj)
			return
		expire_seconds = int(mktime(time_struct) - time.time())

		bot_commands_channel = None
		for channel in ctx.guild.text_channels:
			if channel.name == 'bot_commands_and_misc':
				bot_commands_channel = channel
				break

		if bot_commands_channel is None:
			logger.info("[Reminders remindme()] couldn't find the channel \"bot_commands_and_misc\" to output the reminder to")
			eObj = embed(title='RemindMeIn Error', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="couldn't find the channel \"bot_commands_and_misc\" to output the reminder to!")
			await ctx.send(embed=eObj)
			return

		json_string = json.dumps({'message': message.strip(), 'author_id': ctx.author.id, 'author_name': ctx.author.name})
		r = self.r
		r.set(json_string, '', expire_seconds)
		fmt = 'Reminder set for {0} seconds from now'
		eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description=fmt.format(expire_seconds))
		await ctx.send(embed=eObj)
		logger.info("[Reminders remindme()] reminder has been contructed and sent.")

	@commands.command()
	async def showreminders(self, ctx):
		logger.info("[Reminders showreminders()] remindme command detected from user "+str(ctx.message.author))
		if self.r is not None:
			try:
				reminders=''
				logger.info("[Reminders showreminders()] iterating through all the keys in the database")
				for key in self.r.scan_iter("*"):
					keyValue = json.loads(key)
					logger.info("[Reminders showreminders()] acquired key "+str(keyValue))
					chan = self.bot.get_channel(keyValue['cid'])
					if chan is not None:
						logger.info("[Reminders showreminders()] acquired valid channel "+str(chan))
						msg = await chan.get_message(keyValue['mid'])
						logger.info("[Reminders showreminders()] acquired the messsage "+str(msg))
						reminderCtx = await self.bot.get_context(msg)
						if reminderCtx.valid and helper_files.testenv.TestCog.check_test_environment(reminderCtx):
							if reminderCtx.message.author  == ctx.message.author:
								logger.info("[Reminders showreminders()] determined that message did originate with "+str(ctx.message.author)+", adding to list of reminders")
								reminders+=str(keyValue['mid'])+"\t\t\t"+reminderCtx.message.content+"\n"
				author = ctx.author.nick or ctx.author.name
				if reminders != '':
					logger.info("[Reminders showreminders()] sent off the list of reminders to "+str(ctx.message.author))
					eObj = embed(title="Here are you reminders " + author, author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, content=[["MessageID\t\t\t\t\t\t\tReminder", reminders]])
					await ctx.send(embed=eObj)
				else:
					logger.info("[Reminders showreminders()] "+str(ctx.message.author)+" didnt seem to have any reminders.")
					eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="You don't seem to have any reminders " + author)
					await ctx.send(embed=eObj)
			except Exception as error:
				eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="Something screwy seems to have happened, look at the logs for more info.")
				await ctx.send(embed=eObj)
				logger.error('[Reminders.py showreminders()] Ignoring exception when generating reminder:')
				traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

	@commands.command()
	async def deletereminder(self,ctx,messageId):
		logger.info("[Reminders deletereminder()] deletereminder command detected from user "+str(ctx.message.author))
		if self.r is not None:
			reminderExists=False
			try:
				reminder=''
				logger.info("[Reminders deletereminder()] iterating through all the keys in the database")
				for key in self.r.scan_iter("*"):
					keyValue = json.loads(key)
					logger.info("[Reminders deletereminder()] acquired key "+str(keyValue))
					if keyValue['mid'] == int(messageId):
						reminderExists = True
						logger.info("[Reminders deletereminder()] determined that it was the key the user wants to delete")
						chan = self.bot.get_channel(keyValue['cid'])
						if chan is not None:
							logger.info("[Reminders deletereminder()] acquired valid channel "+str(chan))
							msg = await chan.get_message(keyValue['mid'])
							logger.info("[Reminders deletereminder()] acquired the messsage "+str(msg))
							reminderCtx = await self.bot.get_context(msg)
							if reminderCtx.valid and helper_files.testenv.TestCog.check_test_environment(reminderCtx):
								if reminderCtx.message.author  == ctx.message.author:
									logger.info("[Reminders deletereminder()] determined that message did originate with "+str(ctx.message.author)+", adding to list of reminders")
									reminder=reminderCtx.message.content
									logger.info("[Reminders deletereminder()] following reminder was deleted = "+reminderCtx.message.content)
									eObj = embed(title='Delete Reminder', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="Following reminder has been deleted:\n"+reminder)
									await ctx.send(embed=eObj)
									self.r.delete(key)
								else:
									eObj = embed(title='Delete Reminder', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="ERROR\nYou are trying to delete a reminder that is not yours")
									await ctx.send(embed=eObj)
									logger.info("[Reminders deletereminder()] It seems that  "+str(ctx.message.author)+" was trying to delete "+str(reminderCtx.message.author)+"'s reminder.")
				if not reminderExists:
					eObj = embed(title='Delete Reminder', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="ERROR\nSpecified reminder could not be found")
					await ctx.send(embed=eObj)
					logger.info("[Reminders deletereminder()] Specified reminder could not be found ")
			except Exception as error:
				logger.error('[Reminders.py showreminders()] Ignoring exception when generating reminder:')
				traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

#########################################
## Background function that determines ##
## if a reminder's time has come       ##
## to be sent to its channel           ##
#########################################
	async def get_messages(self):
		await self.bot.wait_until_ready()

		ENVIRONMENT = os.environ['ENVIRONMENT']
		if ENVIRONMENT == 'TEST':
			branch = os.environ['BRANCH'].lower()
			reminder_channel = discord.utils.get(self.bot.guilds[0].channels, name=branch + '_reminder_channel')
			if reminder_channel is None:
				reminder_channel = await self.bot.guilds[0].create_text_channel(branch + '_reminder_channel')
			REMINDER_CHANNEL = reminder_channel.id
		channel = self.bot.get_channel(REMINDER_CHANNEL) # channel ID goes here
		while True:
			message = self.message_subscriber.get_message()
			if message is not None and message['type'] == 'message':
				try:
					reminder_dct = json.loads(message['data'])
					msg = reminder_dct['message']
					author_id = reminder_dct['author_id']
					author_name = reminder_dct['author_name']
					if channel is not None:
						fmt = '<@{0}>\n This is your reminder to "{1}"'
						logger.info('[Misc.py get_message()] sent off reminder to '+str(author_name)+" about \""+msg+"\"")
						await channel.send(fmt.format(author_id, msg))
					else:
						logger.info('[Misc.py get_message()] can\'t find the channel by the id ="'+str(reminder_dct['cid'])+'" to send the reminder to '+str(author_name)+ ' about "'+msg+'"')

				except Exception as error:
					logger.error('[Reminders.py get_message()] Ignoring exception when generating reminder:')
					traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
			await asyncio.sleep(2)

def setup(bot):
	bot.add_cog(Reminders(bot))