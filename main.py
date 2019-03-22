import sys
import traceback
import asyncio
import discord
import logging
import datetime
import pytz
import helper_files.settings as settings
from helper_files import testenv
from helper_files.logger_setup import LoggerWriter
from helper_files.embed import embed as imported_embed
import re
import psycopg2
from discord.ext import commands
import time

bot = commands.Bot(command_prefix='.')
##################
## LOGGING SETUP ##
##################
def initalizeLogger():
	# setting up log requirements
	logger = logging.getLogger('wall_e')
	logger.setLevel(logging.DEBUG)
	formatter = logging.Formatter('%(asctime)s = %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')
	stream_handler = logging.StreamHandler()
	stream_handler.setLevel(logging.DEBUG)
	stream_handler.setFormatter(formatter)
	logger.addHandler(stream_handler)
	sys.stdout = LoggerWriter(logger, logging.INFO)
	sys.stderr = LoggerWriter(logger, logging.WARNING)
	createLogFile(formatter, logger)
	return logger

def createLogFile(formatter,logger):
	DATE=datetime.datetime.now(pytz.timezone('US/Pacific')).strftime("%Y_%m_%d_%H_%M_%S")
	global FILENAME
	FILENAME="logs/"+DATE+"_wall_e"
	filehandler=logging.FileHandler("{}.log".format(FILENAME))
	filehandler.setLevel(logging.INFO)
	filehandler.setFormatter(formatter)
	logger.addHandler(filehandler)

###############################
## SETUP DATABASE CONNECTION ##
###############################

def setupDB():
	try:
		host=None
		if 'localhost' == settings.ENVIRONMENT:
			host='127.0.0.1'
		else:
			host=settings.COMPOSE_PROJECT_NAME+'_wall_e_db'
		dbConnectionString="dbname='"+settings.POSTGRES_DB_DBNAME+"' user='"+settings.POSTGRES_DB_USER+"' host='"+host+"' password='"+settings.POSTGRES_PASSWORD+"'"
		logger.info("[main.py setupDB] Postgres User dbConnectionString=[dbname='"+settings.POSTGRES_DB_DBNAME+"' user='"+settings.POSTGRES_DB_USER+"' host='"+host+"' password='*****']")
		postgresConn = psycopg2.connect(dbConnectionString)
		logger.info("[main.py setupDB] PostgreSQL connection established")
		postgresConn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
		postgresCurs = postgresConn.cursor()

		#these two parts is using a complicated DO statement because apparently postgres does not have an "if not exist" clause for roles or databases, only tables
		#moreover, this is done to localhost and not any other environment cause with the TEST guild, the databases are always brand new fresh with each time the script get launched
		if 'localhost' == settings.ENVIRONMENT or'PRODUCTION' == settings.ENVIRONMENT:
			#aquired from https://stackoverflow.com/a/8099557/7734535
			sqlQuery="""DO
						$do$
						BEGIN
							IF NOT EXISTS (
								SELECT                       -- SELECT list can stay empty for this
								FROM   pg_catalog.pg_roles
								WHERE  rolname = '"""+settings.WALL_E_DB_USER+"""') THEN
								CREATE ROLE """+settings.WALL_E_DB_USER+""" WITH NOSUPERUSER INHERIT NOCREATEROLE NOCREATEDB LOGIN NOREPLICATION NOBYPASSRLS ENCRYPTED PASSWORD '"""+settings.WALL_E_DB_PASSWORD+"""';
							END IF;
						END
						$do$;"""
			postgresCurs.execute(sqlQuery)
		else:
			postgresCurs.execute("CREATE ROLE "+settings.WALL_E_DB_USER+" WITH NOSUPERUSER INHERIT NOCREATEROLE NOCREATEDB LOGIN NOREPLICATION NOBYPASSRLS ENCRYPTED PASSWORD '"+settings.WALL_E_DB_PASSWORD+"';")
		logger.info("[main.py setupDB] "+settings.WALL_E_DB_USER+" role created")

		if 'localhost' == settings.ENVIRONMENT or 'PRODUCTION' == settings.ENVIRONMENT:
			sqlQuery="""SELECT datname from pg_database"""
			postgresCurs.execute(sqlQuery)
			results = postgresCurs.fetchall()

			#fetchAll returns  [('postgres',), ('template0',), ('template1',), ('csss_discord_db',)]
			#which the below line converts to  ['postgres', 'template0', 'template1', 'csss_discord_db']
			results = [x for xs in results for x in xs]

			if settings.WALL_E_DB_DBNAME not in results:
				postgresCurs.execute("CREATE DATABASE "+settings.WALL_E_DB_DBNAME+" WITH OWNER "+settings.WALL_E_DB_USER+" TEMPLATE = template0;")
				logger.info("[main.py setupDB] "+settings.WALL_E_DB_DBNAME+" database created")
			else:
				logger.info("[main.py setupDB] "+settings.WALL_E_DB_DBNAME+" database already exists")
		else:
			postgresCurs.execute("CREATE DATABASE "+settings.WALL_E_DB_DBNAME+" WITH OWNER "+settings.WALL_E_DB_USER+" TEMPLATE = template0;")
			logger.info("[main.py setupDB] "+settings.WALL_E_DB_DBNAME+" database created")

		#this section exists cause of this backup.sql that I had exported from an instance of a Postgres with which I had created the csss_discord_db
		#https://github.com/CSSS/wall_e/blob/implement_postgres/helper_files/backup.sql#L31
		dbConnectionString="dbname='"+settings.WALL_E_DB_DBNAME+"' user='"+settings.POSTGRES_DB_USER+"' host='"+host+"' password='"+settings.POSTGRES_PASSWORD+"'"
		logger.info("[main.py setupDB] Wall_e User dbConnectionString=[dbname='"+settings.WALL_E_DB_DBNAME+"' user='"+settings.POSTGRES_DB_USER+"' host='"+host+"' password='*****']")
		walleConn = psycopg2.connect(dbConnectionString)
		logger.info("[main.py setupDB] PostgreSQL connection established")
		walleConn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
		walleCurs = walleConn.cursor()
		walleCurs.execute("SET statement_timeout = 0;")
		walleCurs.execute("SET default_transaction_read_only = off;")
		walleCurs.execute("SET lock_timeout = 0;")
		walleCurs.execute("SET idle_in_transaction_session_timeout = 0;")
		walleCurs.execute("SET client_encoding = 'UTF8';")
		walleCurs.execute("SET standard_conforming_strings = on;")
		walleCurs.execute("SELECT pg_catalog.set_config('search_path', '', false);")
		walleCurs.execute("SET check_function_bodies = false;")
		walleCurs.execute("SET client_min_messages = warning;")
		walleCurs.execute("SET row_security = off;")
		walleCurs.execute("CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;")
		walleCurs.execute("COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';")
	except Exception as e:
		logger.error("[main.py setupDB] enountered following exception when setting up PostgreSQL connection\n{}".format(e))

##################################################
## signals to all functions that use            ##
## "wait_until_ready" that the bot is now ready ##
## to start performing background tasks         ##
##################################################

@bot.event
async def on_ready():
	logger.info('[main.py on_ready()] Logged in as')
	logger.info('[main.py on_ready()] '+bot.user.name)
	logger.info('[main.py on_ready()] '+str(bot.user.id))
	logger.info('[main.py on_ready()] ------')

	settings.BOT_NAME = bot.user.name
	settings.BOT_AVATAR = bot.user.avatar_url
	logger.info('[main.py on_ready()] BOT_NAME initialized to '+str(settings.BOT_NAME)+ ' in settings.py')
	logger.info('[main.py on_ready()] BOT_AVATAR initialized to '+str(settings.BOT_AVATAR)+ ' in settings.py')

	logger.info('[main.py on_ready()] '+bot.user.name+' is now ready for commands')

##################################################################################################
## HANDLES BACKGROUND TASK OF WRITING CONTENTS OF LOG FILE TO BOT_LOG CHANNEL ON DISCORD SERVER ##
##################################################################################################
async def write_to_bot_log_channel():
	await bot.wait_until_ready()

	# only environment that doesn't do automatic creation of the bot_log channel is the PRODUCTION guild.
	# Production is a permanant channel so that it can be persistent. As for localhost,
	# the idea was that this removes a dependence on the user to make the channel and shifts that responsibility to the script itself.
	# thereby requiring less effort from the user
	bot_log_channel = None
	if settings.ENVIRONMENT != 'PRODUCTION':
		
		log_channel_name=''
		if settings.ENVIRONMENT == 'TEST':
			log_channel_name=settings.BRANCH_NAME.lower() + '_logs'
		else:
			log_channel_name=settings.ENVIRONMENT.lower() + '_logs'

		log_channel = discord.utils.get(bot.guilds[0].channels, name=log_channel_name)

		if log_channel is None:
			log_channel = await bot.guilds[0].create_text_channel(log_channel_name)
		bot_log_channel = log_channel.id
	else:
		bot_log_channel = settings.BOT_LOG_CHANNEL
	channel = bot.get_channel(bot_log_channel) # channel ID goes here
	
	if channel is None:
		logger.error("[main.py write_to_bot_log_channel] could not retrieve the bot_log channel with id " +str(bot_log_channel) +" . Please investigate further")
	else:
		logger.info("[main.py write_to_bot_log_channel] bot_log channel with id " +str(bot_log_channel) +" successfully retrieved.")
		while not bot.is_closed():
			f.flush()
			line = f.readline()
			while line:
				if line.strip() != "":

					#this was done so that no one gets accidentally pinged from the bot log channel
					line=line.replace("@","[at]")
					if line[0] == ' ':
						line = "." + line
					output=line

					#done because discord has a character limit of 2000 for each message
					if len(line)>2000:
						prefix="truncated output="
						line = prefix+line
						length = len(line)- (len(line) - 2000) #taking length of just output into account
						length = length - len(prefix) #taking length of prefix into account
						output=line[:length]
					await channel.send(output)
				line = f.readline()
			await asyncio.sleep(1)

####################################################
## Function that gets called when the script cant ##
## understand the command that the user invoked   ##
####################################################
@bot.event
async def on_command_error(ctx, error):
	if testenv.TestCog.check_test_environment(ctx):
		if isinstance(error, commands.MissingRequiredArgument):
			fmt = 'Missing argument: {0}'
			logger.error('[main.py on_command_error()] '+fmt.format(error.param))
			eObj = imported_embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description=fmt.format(error.param))
			await ctx.send(embed=eObj)
		else:
			#only prints out an error to the log if the string that was entered doesnt contain just "."
			pattern = r'[^\.]'
			if re.search(pattern, str(error)[9:-14]):
					author = ctx.author.nick or ctx.author.name
					#await ctx.send('Error:\n```Sorry '+author+', seems like the command \"'+str(error)[9:-14]+'\"" doesn\'t exist :(```')
					traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
					return

def setupStatsOfCommandsDBTable():
	try:
		host=None
		if 'localhost' == settings.ENVIRONMENT:
			host='127.0.0.1'
		else:
			host=settings.COMPOSE_PROJECT_NAME+'_wall_e_db'
		dbConnectionString="dbname='csss_discord_db' user='wall_e' host='"+host+"' password='"+settings.WALL_E_DB_PASSWORD+"'"
		logger.info("[main.py setupStatsOfCommandsDBTable()] dbConnectionString=[dbname='csss_discord_db' user='wall_e' host='"+host+"' password='******']")
		conn = psycopg2.connect(dbConnectionString)
		logger.info("[main.py setupStatsOfCommandsDBTable()] PostgreSQL connection established")
		conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
		curs = conn.cursor()
		curs.execute("CREATE TABLE IF NOT EXISTS CommandStats ( \"EPOCH TIME\" BIGINT  PRIMARY KEY, YEAR BIGINT, MONTH BIGINT, DAY BIGINT, HOUR BIGINT, \"Channel ID\" BIGINT, \"Channel Name\" varchar(2000), Author varchar(2000), Command varchar(2000), Argument varchar(2000), \"Invoked with\" varchar(2000), \"Invoked subcommand\"  varchar(2000));")
		logger.info("[main.py setupStatsOfCommandsDBTable()] CommandStats database table created")
	except Exception as e:
		logger.error("[main.py setupStatsOfCommandsDBTable()] enountered following exception when setting up PostgreSQL connection\n{}".format(e))

########################################################
## Function that gets called whenever a commmand      ##
## gets called, being use for data gathering purposes ##
########################################################
@bot.event
async def on_command(ctx):
	if testenv.TestCog.check_test_environment(ctx):
		try:
			host=None
			if 'localhost' == settings.ENVIRONMENT:
				host='127.0.0.1'
			else:
				host=settings.COMPOSE_PROJECT_NAME+'_wall_e_db'
			dbConnectionString="dbname='csss_discord_db' user='wall_e' host='"+host+"' password='"+settings.WALL_E_DB_PASSWORD+"'"
			logger.info("[main.py on_command()] dbConnectionString=[dbname='csss_discord_db' user='wall_e' host='"+host+"' password='******']")
			conn = psycopg2.connect(dbConnectionString)
			logger.info("[main.py on_command()] PostgreSQL connection established")
			conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
			curs = conn.cursor()
			index=0
			for arg in ctx.args:
				if index > 1:
					argument += arg+' '
				index+=1
			epoch_time = str(int(time.time()))

			now = datetime.datetime.now()
			current_year=str(now.year)
			current_month=str(now.month)
			current_day=str(now.day)
			current_hour=str(now.hour)
			channel_id=str(ctx.channel.id)
			channel_name=str(ctx.channel).replace("\'","[single_quote]").strip()
			if ctx.guild.get_member(ctx.message.author.id).name.isalnum():
				author=str(ctx.message.author).replace("\'","[single_quote]").strip()
			else:
				author="<"+str(ctx.message.author.id).replace("\'","[single_quote]").strip()+">"
			command=str(ctx.command).replace("\'","[single_quote]").strip()
			argument=str(argument).replace("\'","[single_quote]").strip() if command is not "embed" else "redacted due to large size"
			method_of_invoke=str(ctx.invoked_with).replace("\'","[single_quote]").strip()
			invoked_subcommand=str(ctx.invoked_subcommand).replace("\'","[single_quote]").strip()

			#this next part is just setup to keep inserting until it finsd a primary key that is not in use
			successful=False
			while not successful:
				try:
					sqlCommand="""INSERT INTO CommandStats ( \"EPOCH TIME\", YEAR, MONTH, DAY, HOUR, \"Channel ID\", \"Channel Name\", Author, Command, Argument, \"Invoked with\", \"Invoked subcommand\") 
					VALUES ("""+str(epoch_time)+""","""+current_year+""", """+current_month+""","""+current_day+""","""+current_hour+""","""+channel_id+""",
					'"""+channel_name+"""','"""+author+"""', '"""+command+"""','"""+argument+"""',
					'"""+method_of_invoke+"""','"""+invoked_subcommand+"""');"""
					logger.info("[main.py on_command()] sqlCommand=["+sqlCommand+"]")
					curs.execute(sqlCommand)
				except psycopg2.IntegrityError as e:
					logger.error("[main.py on_command()] enountered following exception when trying to insert the record\n{}".format(e))	
					epoch_time += 1
					logger.info("[main.py on_command()] incremented the epoch time to "+str(epoch_time)+" and will try again.")	
				else:
					successful=True
			curs.close()
			conn.close()
		except Exception as e:
			logger.error("[main.py on_command()] enountered following exception when setting up PostgreSQL connection\n{}".format(e))	



########################################################
## Function that gets called any input or output from ##
## the script										  ##
########################################################
@bot.event
async def on_message(message):
	if message.guild is None and message.author != bot.user:
		await message.author.send("DM has been detected \nUnfortunately none of my developers are smart enough to make me an AI capable of holding a conversation and no one else has volunteered :( \nAll I can say is Harry Potter for life and Long Live Windows Vista!")
	else:
		await bot.process_commands(message)

@bot.listen()
async def on_member_join(member):

	if member is not None:
		output="Hi, welcome to the SFU CSSS Discord Server\n"
		output+="\tWe are a group of students who live to talk about classes and nerdy stuff.\n"
		output+="\tIf you need help, please ping any of our Execs, Execs at large, or First Year Reps.\n"
		output+="\n"
		output+="\tOur general channels include some of the following:\n"
		output+="\t#off-topic, where we discuss damn near anything.\n"
		output+="\t#first-years, for students who are starting, or about to start their first year.\n"
		output+="\t#discussion, for serious non-academic discussion. (Politics et al.)\n"
		output+="\t#sfu-discussions, for all SFU related discussion.\n"
		output+="\t#projects_and_dev, for non-academic tech/dev/project discussion.\n"
		output+="\t#bot_commands_and_misc, for command testing to reduce spam on other channels.\n"
		output+="\n"
		output+="\n"
		output+="\tWe also have a smattering of course specific Academic channels.\n"
		output+="\tYou can give yourself a class role by running <.iam cmpt320> or create a new class by <.newclass cmpt316>\n"
		output+="\tPlease keep Academic Honesty in mind when discussing course material here.\n"
		eObj = imported_embed(description=output, author=settings.BOT_NAME, avatar=settings.BOT_AVATAR)
		await member.send(embed=eObj)
		logger.info("[main.py on_member_join] embed sent to member "+str(member))

####################
## STARTING POINT ##
####################
if __name__ == "__main__":
	FILENAME = None
	logger = initalizeLogger()
	logger.info("[main.py] Wall-E is starting up")
	setupDB()
	setupStatsOfCommandsDBTable()

	## tries to open log file in prep for write_to_bot_log_channel function
	try:
		logger.info("[main.py] trying to open "+FILENAME+".log to be able to send its output to #bot_log channel")
		f = open(FILENAME+'.log', 'r')
		f.seek(0)
		bot.loop.create_task(write_to_bot_log_channel())
		logger.info("[main.py] log file successfully opened and connection to bot_log channel has been made")
	except Exception as e:
		logger.error("[main.py] Could not open log file to read from and sent entries to bot_log channel due to following error"+str(e))

	# load the code dealing with test server interaction
	try:
		bot.load_extension('helper_files.testenv')
	except Exception as e:
		exception = '{}: {}'.format(type(e).__name__, e)
		logger.error('[main.py] Failed to load test server code testenv\n{}'.format(exception))

	#removing default help command to allow for custom help command
	logger.info("[main.py] default help command being removed")
	bot.remove_command("help")

	## tries to loads any commands specified in the_commands into the bot
	for cog in settings.cogs:
		commandLoaded=True
		try:
			logger.info("[main.py] attempting to load command "+ cog["name"])
			bot.load_extension(cog["folder"] + '.' + cog["name"])
		except Exception as e:
			commandLoaded=False
			exception = '{}: {}'.format(type(e).__name__, e)
			logger.error('[main.py] Failed to load command {}\n{}'.format(cog["name"], exception))
		if commandLoaded:
			logger.info("[main.py] " + cog["name"] + " successfully loaded")

	##final step, running the bot with the passed in environment TOKEN variable
	bot.run(settings.TOKEN)
