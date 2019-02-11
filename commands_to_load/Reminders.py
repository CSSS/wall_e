import discord
from discord.ext import commands
import discord
import json
import logging
import asyncio
import parsedatetime
import time
from time import mktime
import helper_files.testenv
import traceback
import sys
import helper_files.settings as settings
from helper_files.embed import embed
import psycopg2
import os
import datetime
from main import ENVIRONMENT
logger = logging.getLogger('wall_e')

COMPOSE_PROJECT_NAME = os.environ['COMPOSE_PROJECT_NAME']
logger.info("[main.py] variable \"COMPOSE_PROJECT_NAME\" is set to \""+str(COMPOSE_PROJECT_NAME)+"\"")

WALL_E_DB_PASSWORD = os.environ['WALL_E_DB_PASSWORD']
logger.info("[main.py] variable \"WALL_E_DB_PASSWORD\" is set to \""+str(WALL_E_DB_PASSWORD)+"\"")

class Reminders():

	def __init__(self, bot):
		self.bot = bot

		#setting up database connection
		try:
			conn = psycopg2.connect("dbname='csss_discord_db' user='wall_e' host='"+COMPOSE_PROJECT_NAME+"_wall_e_db' password='"+WALL_E_DB_PASSWORD+"'")
			conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
			self.curs = conn.cursor()
			#self.curs.execute("DROP TABLE IF EXISTS Reminders;")
			self.curs.execute("CREATE TABLE IF NOT EXISTS Reminders ( reminder_id BIGSERIAL  PRIMARY KEY, reminder_date timestamp, message varchar(2000), author_id varchar(500), author_name varchar(500), message_id varchar(200));")
			self.bot.loop.create_task(self.get_messages())
			logger.info("[Reminders __init__] PostgreSQL connection established")
		except Exception as e:
			logger.error("[Reminders __init__] enountered following exception when setting up PostgreSQL connection\n{}".format(e))


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

		expire_seconds = int(mktime(time_struct) - time.time())
		dt = datetime.datetime.now()
		b = dt + datetime.timedelta(seconds=expire_seconds) # days, seconds, then other fields.

		sqlCommand="INSERT INTO Reminders (  reminder_date, message, author_id, author_name, message_id) VALUES (TIMESTAMP '"+str(b)+"', '"+message+"', '"+str(ctx.author.id)+"', '"+str(ctx.message.author)+"',  '"+str(ctx.message.id)+"');"

		logger.info("[Reminders remindme()] sqlCommand=["+sqlCommand+"]")
		self.curs.execute(sqlCommand)
		fmt = 'Reminder set for {0} seconds from now'

		eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description=fmt.format(expire_seconds))
		await ctx.send(embed=eObj)
		logger.info("[Reminders remindmein()] reminder has been contructed and sent.")

	@commands.command()
	async def showreminders(self, ctx):
		logger.info("[Reminders showreminders()] remindme command detected from user "+str(ctx.message.author))
		if self.curs is not None:
			try:
				reminders=''
				sqlCommand = "SELECT * FROM Reminders WHERE author_id = '"+str(ctx.author.id)+"';"
				self.curs.execute(sqlCommand)
				logger.info("[Reminders showreminders()] retrieved all reminders belonging to user "+str(ctx.message.author))
				for row in self.curs.fetchall():
					logger.info("[Reminders showreminders()] dealing with reminder ["+str(row)+"]")
					reminders+=str(row[5])+"\t\t\t"+str(row[2])+"\n"
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
		try:
			if self.curs is not None:
				sqlCommand = "SELECT * FROM Reminders WHERE message_id = '"+str(messageId)+"';"
				self.curs.execute(sqlCommand)
				result = self.curs.fetchone()
				print("result="+str(result))
				if result is None:
					eObj = embed(title='Delete Reminder', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="ERROR\nSpecified reminder could not be found")
					await ctx.send(embed=eObj)
					logger.info("[Reminders deletereminder()] Specified reminder could not be found ")
				else:
					if str(result[4]) == str(ctx.message.author):
					##check to make sure its the right author
						sqlCommand = "DELETE FROM Reminders WHERE message_id = '"+str(messageId)+"';"
						self.curs.execute(sqlCommand)
						logger.info("[Reminders deletereminder()] following reminder was deleted = "+str(result))
						eObj = embed(title='Delete Reminder', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="Following reminder has been deleted:\n"+str(result[2]))
						await ctx.send(embed=eObj)
					else:
						eObj = embed(title='Delete Reminder', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="ERROR\nYou are trying to delete a reminder that is not yours")
						await ctx.send(embed=eObj)
						logger.info("[Reminders deletereminder()] It seems that  "+str(ctx.message.author)+" was trying to delete "+str(result[4])+"'s reminder.")						
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

		REMINDER_CHANNEL_ID=None
		BRANCH = None
		if ENVIRONMENT == 'TEST' and 'BRANCH' not in os.environ:
			print("[Reminders.py get_messages()] No environment variable \"BRANCH\" seems to exist and this is the discord TEST guild...read the README again")
			exit(1)	
		elif ENVIRONMENT == 'TEST'  and 'BRANCH' in os.environ:
			BRANCH = os.environ['BRANCH']

		##determines the channel to send the reminder on
		try:
			if ENVIRONMENT == 'PRODUCTION':
				logger.info("[Reminders get_messages()] environment is =["+ENVIRONMENT+"]")
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
				logger.info("[Reminders get_messages()] branch is =["+BRANCH+"]")
				reminder_chan = discord.utils.get(self.bot.guilds[0].channels, name=BRANCH.lower()+'_reminders')
				if reminder_chan is None:
					reminder_chan = await self.bot.guilds[0].create_text_channel(BRANCH+'_reminders')
					REMINDER_CHANNEL_ID = reminder_chan.id
					if REMINDER_CHANNEL_ID is None:
						logger.info("[Reminders get_messages()] the channel designated for reminders ["+BRANCH+"_reminders] in "+str(BRANCH)+" does not exist and I was unable to create it, exiting now....")
						exit(1)
					logger.info("[Reminders get_messages()] variable \"REMINDER_CHANNEL_ID\" is set to \""+str(REMINDER_CHANNEL_ID)+"\"")
				else:
					logger.info("[Reminders get_messages()] reminder channel exists in "+str(BRANCH)+" and was detected.")
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
			dt = datetime.datetime.now()
			try:
				self.curs.execute("SELECT * FROM Reminders where reminder_date <= TIMESTAMP '"+str(dt)+"';")
				for row in self.curs.fetchall():
					print(row)
					#fmt = '<@{0}>\n {1}'
					fmt = '{0}'
					reminder_message = row[2]
					author_id = row[3]
					logger.info('[Misc.py get_message()] obtained the message of ['+str(reminder_message)+'] for author with id ['+str(author_id)+'] for REMINDER_CHANNEL ['+str(REMINDER_CHANNEL_ID)+']')
					reminder_channel = self.bot.get_channel(int(REMINDER_CHANNEL_ID))
					logger.info('[Misc.py get_message()] sent off reminder to '+str(author_id)+" about \""+reminder_message+"\"")
					eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description="This is your reminder to "+reminder_message, footer='Reminder')
					self.curs.execute("DELETE FROM Reminders WHERE reminder_id = "+str(row[0])+";")
					await reminder_channel.send('<@'+author_id+'>',embed=eObj)
			except Exception as error:
				logger.error('[Reminders.py get_message()] Ignoring exception when generating reminder:')
				traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
			await asyncio.sleep(2)

def setup(bot):
	bot.add_cog(Reminders(bot))
