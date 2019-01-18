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
from main import ENVIRONMENT
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
		fmt = 'I am offline, sorry.'
		eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description=fmt)
		await ctx.send(embed=eObj)
		logger.info("[Reminders remindme()] offline message has been sent.")

	@commands.command()
	async def showreminders(self, ctx):
		logger.info("[Reminders remindme()] remindme command detected from user "+str(ctx.message.author))
		fmt = 'I am offline, sorry.'
		eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description=fmt)
		await ctx.send(embed=eObj)
		logger.info("[Reminders remindme()] offline message has been sent.")

	@commands.command()
	async def deletereminder(self,ctx,messageId):
		logger.info("[Reminders remindme()] remindme command detected from user "+str(ctx.message.author))
		fmt = 'I am offline, sorry.'
		eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description=fmt)
		await ctx.send(embed=eObj)
		logger.info("[Reminders remindme()] offline message has been sent.")

#########################################
## Background function that determines ##
## if a reminder's time has come       ##
## to be sent to its channel           ##
#########################################
	async def get_messages(self):
		await self.bot.wait_until_ready()

		REMINDER_CHANNEL_ID=None
		##determines the channel to send the reminder on
		try:
			if ENVIRONMENT == 'PRODUCTION':
				branch = os.environ['BRANCH'].lower()
				logger.info("[Reminders get_messages()] branch is =["+branch+"]")
				reminder_chan = discord.utils.get(self.bot.guilds[0].channels, name='bot_commands_and_misc')
				if reminder_chan is None:
					logger.info("[Reminders get_messages()] reminder channel does not exist in PRODUCTION.")
					reminder_chan = await self.bot.guilds[0].create_text_channel('bot_commands_and_misc')
					REMINDER_CHANNEL_ID = reminder_chan.id
					if REMINDER_CHANNEL_ID is None:
						logger.info("[Reminders get_messages()] the channel designated for reminders [bot_commands_and_misc] in PRODUCTION does not exist and I was unable to create it, exiting now....")
						exit(1)
					logger.info("[Reminders get_messages()] variable \"REMINDER_CHANNEL_ID\" is set to \""+str(REMINDER_CHANNEL_ID)+"\"")
				else:
					logger.info("[Reminders get_messages()] reminder channel exists in PRODUCTION and was detected.")
					REMINDER_CHANNEL_ID = reminder_chan.id
       
			elif ENVIRONMENT == 'TEST':
				branch = os.environ['BRANCH'].lower()
				logger.info("[Reminders get_messages()] branch is =["+branch+"]")
				reminder_chan = discord.utils.get(self.bot.guilds[0].channels, name=branch+'_reminders')
				if reminder_chan is None:
					reminder_chan = await self.bot.guilds[0].create_text_channel(branch+'_reminders')
					REMINDER_CHANNEL_ID = reminder_chan.id
					if REMINDER_CHANNEL_ID is None:
						logger.info("[Reminders get_messages()] the channel designated for reminders ["+branch+"_reminders] in "+str(branch)+" does not exist and I was unable to create it, exiting now....")
						exit(1)
					logger.info("[Reminders get_messages()] variable \"REMINDER_CHANNEL_ID\" is set to \""+str(REMINDER_CHANNEL_ID)+"\"")
				else:
					logger.info("[Reminders get_messages()] reminder channel exists in "+str(branch)+" and was detected.")
					REMINDER_CHANNEL_ID = reminder_chan.id
			else:
				reminder_chan = discord.utils.get(self.bot.guilds[0].channels, name='reminders')
				if reminder_chan is None:
					reminder_chan = await self.bot.guilds[0].create_text_channel('reminders')
					REMINDER_CHANNEL_ID = reminder_chan.id
					if REMINDER_CHANNEL_ID is None:
						logger.info("[Reminders get_messages()] the channel designated for reminders [reminders] does not exist and I was unable to create it, exiting now....")
						exit(1)
					logger.info("[Reminders get_messages()] variable \"REMINDER_CHANNEL_ID\" is set to \""+str(REMINDER_CHANNEL_ID)+"\"")
				else:
					logger.info("[Reminders get_messages()] reminder channel exists and was detected.")
					REMINDER_CHANNEL_ID = reminder_chan.id
		except Exception as e:
			logger.error("[Reminders get_messages()] enountered following exception when connecting to reminder channel\n{}".format(e))
		
		REMINDER_CHANNEL = self.bot.get_channel(REMINDER_CHANNEL_ID) # channel ID goes here
		
		while True:
			message = self.message_subscriber.get_message()
			if message is not None and message['type'] == 'message':
				try:
					reminder_dct = json.loads(message['data'])
					if 'env' in reminder_dct:
						msg = reminder_dct['message']
						author_id = reminder_dct['author_id']
						author_name = reminder_dct['author_name']
						if REMINDER_CHANNEL is not None:
							#fmt = '<@{0}>\n This is your reminder to ```"{1}"```'
							fmt = 'This is your reminder to "{0}"'
							logger.info('[Reminders.py get_message()] sent off reminder to '+str(author_name)+" about \""+msg+"\"")
							eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description=fmt.format(msg), footer='Reminder')
							await REMINDER_CHANNEL.send("<@"+str(author_id)+">",embed=eObj)
						else:
							logger.info('[Reminders.py get_message()] It seems that "REMINDER_CHANNEL" ='+str(REMINDER_CHANNEL)+' doesn\'t exist so I can\'t send the reminder to "'+str(author_name)+'" about "'+msg+'"')

				except Exception as error:
					logger.error('[Reminders.py get_message()] Ignoring exception when generating reminder:')
					traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
			await asyncio.sleep(2)

def setup(bot):
	bot.add_cog(Reminders(bot))
