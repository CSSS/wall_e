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

			self.env=ENVIRONMENT
			if 'branch' in os.environ:
				self.branch=os.environ['BRANCH'].lower()
			else:
				self.branch = ''
			self.bot.loop.create_task(self.get_messages())
			logger.info("[Reminders __init__] redis connection established")
		except Exception as e:
			logger.error("[Reminders __init__] enountered following exception when setting up redis connection\n{}".format(e))


	@commands.command()
	async def remindmein(self, ctx, *args):
		logger.info("[Reminders remindmein()] remindme command detected from user "+str(ctx.message.author))
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
			logger.info("[Reminders remindmein()] was unable to extract a time")
			eObj = embed(title='RemindMeIn Error', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="unable to extract a time"+str(how_to_call_command))
			await ctx.send(embed=eObj)
			return
		if message == '':
			logger.info("[Reminders remindmein()] was unable to extract a message")
			eObj = embed(title='RemindMeIn Error', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="unable to extract a string"+str(how_to_call_command))
			await ctx.send(embed=eObj)
			return
		timeUntil = str(parsedTime)
		logger.info("[Reminders remindmein()] extracted time is "+str(timeUntil))
		logger.info("[Reminders remindmein()] extracted message is "+str(message))
		time_struct, parse_status = parsedatetime.Calendar().parse(timeUntil)
		if parse_status == 0:
			logger.info("[Reminders remindmein()] couldn't parse the time")
			eObj = embed(title='RemindMeIn Error', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="Could not parse time!"+how_to_call_command)
			await ctx.send(embed=eObj)
			return

		#sets when the reminder should expire
		expire_seconds = int(mktime(time_struct) - time.time())


		json_string = json.dumps({'message': message.strip(), 'author_id': ctx.author.id, 'author_name': str(ctx.message.author), 'message_id': ctx.message.id, 'env': self.env, 'branch': self.branch})
		r = self.r
		r.set(json_string, '', expire_seconds)
		fmt = 'Reminder set for {0} seconds from now'

		eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description=fmt.format(expire_seconds))
		await ctx.send(embed=eObj)
		logger.info("[Reminders remindmein()] reminder has been contructed and sent.")

	@commands.command()
	async def showreminders(self, ctx):
		logger.info("[Reminders showreminders()] remindme command detected from user "+str(ctx.message.author))
		if self.r is not None:
			try:
				reminders=''
				logger.info("[Reminders showreminders()] iterating through all the keys in the database")
				for key in self.r.scan_iter("*"):
					keyValue = json.loads(key)
					if 'message' in keyValue and 'author_id' in keyValue and 'author_name' in keyValue and 'message_id' in keyValue and 'env' in keyValue and 'branch' in keyValue:
					#this test is done in case there are any reminders still in the database that use the old format
					# this check will make sure that they are ignored
						
						logger.info("[Reminders showreminders()] acquired reminder=["+str(keyValue)+"]")
						logger.info("[Reminders showreminders()] ctx.message.author=["+str(ctx.message.author)+"]")
						logger.info("[Reminders showreminders()] ENVIRONMENT=["+str(ENVIRONMENT)+"]")
						
						
						msg = keyValue['message']
						env = keyValue['env']
						branch = keyValue['branch']
						author_name = keyValue['author_name']
						
						validAuthor = str(ctx.message.author) == str(author_name) #check to ensure that the current reminder its going through belongs to the person who called the command
						validDiscordGuild = self.env == env #checks to make sure that the guild indicate by the reminder is the guild that the command was called from
						
						validBranch = branch == self.branch

						validEnv = ( str(ENVIRONMENT) == str(env) )
						if 	validAuthor and validDiscordGuild and validBranch:
							logger.info("[Reminders showreminders()] determined that message did originate with "+str(ctx.message.author)+", adding to list of reminders")
							reminders+=str(keyValue['message_id'])+"\t\t\t"+msg+"\n"
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
					if 'message' in keyValue and 'author_id' in keyValue and 'author_name' in keyValue and 'message_id' in keyValue and 'env' in keyValue and 'branch' in keyValue:
					#this test is done in case there are any reminders still in the database that use the old format
					# this check will make sure that they are ignored
						logger.info("[Reminders deletereminder()] acquired reminder=["+str(keyValue)+"]")
						msg = keyValue['message']
						env = keyValue['env']
						author_name = keyValue['author_name']
						author_id = keyValue['author_id']
						message_id = keyValue['message_id']
						branch = keyValue['branch']
						
						if message_id == int(messageId):
							reminderExists = True
							logger.info("[Reminders deletereminder()] determined that it was the key the user wants to delete")

							validAuthor = str(ctx.message.author) == str(author_name) #check to ensure that the current reminder its going through belongs to the person who called the command
							validDiscordGuild = self.env == env  #checks to make sure that the guild indicate by the reminder is the guild that the command was called from
							
							validBranch = branch == self.branch

							if validAuthor:
								if validDiscordGuild and validBranch:
									logger.info("[Reminders deletereminder()] determined that message did originate with "+str(ctx.message.author)+", adding to list of reminders")
									logger.info("[Reminders deletereminder()] following reminder was deleted = "+msg)
									eObj = embed(title='Delete Reminder', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="Following reminder has been deleted:\n"+msg)
									await ctx.send(embed=eObj)
									self.r.delete(key)
								else:
									logger.info("[Reminders deletereminder()] It seems that  "+str(ctx.message.author)+" was trying to a reminder from another environment or branch.")								
							else:
								eObj = embed(title='Delete Reminder', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="ERROR\nYou are trying to delete a reminder that is not yours")
								await ctx.send(embed=eObj)
								logger.info("[Reminders deletereminder()] It seems that  "+str(ctx.message.author)+" was trying to delete "+str(author_name)+"'s reminder.")
				if not reminderExists:
					eObj = embed(title='Delete Reminder', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="ERROR\nSpecified reminder could not be found")
					await ctx.send(embed=eObj)
					logger.info("[Reminders deletereminder()] Specified reminder could not be found ")
			except Exception as error:
				logger.error('[Reminders.py deletereminder()] Ignoring exception when generating reminder:')
				traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

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
				logger.info("[Reminders get_messages()] branch is =["+self.branch+"]")
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
				logger.info("[Reminders get_messages()] branch is =["+self.branch+"]")
				reminder_chan = discord.utils.get(self.bot.guilds[0].channels, name=self.branch+'_reminders')
				if reminder_chan is None:
					reminder_chan = await self.bot.guilds[0].create_text_channel(self.branch+'_reminders')
					REMINDER_CHANNEL_ID = reminder_chan.id
					if REMINDER_CHANNEL_ID is None:
						logger.info("[Reminders get_messages()] the channel designated for reminders ["+self.branch+"_reminders] in "+str(self.branch)+" does not exist and I was unable to create it, exiting now....")
						exit(1)
					logger.info("[Reminders get_messages()] variable \"REMINDER_CHANNEL_ID\" is set to \""+str(REMINDER_CHANNEL_ID)+"\"")
				else:
					logger.info("[Reminders get_messages()] reminder channel exists in "+str(self.branch)+" and was detected.")
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
