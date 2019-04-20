from discord.ext import commands
import discord
import subprocess
import helper_files.settings as settings
import csv
import logging
import matplotlib.pyplot as plt
import numpy as np
import operator
import psycopg2
import asyncio
from helper_files.send import send as send

logger = logging.getLogger('wall_e')

class Administration():

	def __init__(self, bot):
		self.bot = bot

	def validCog(self, name):
		for cog in settings.cogs:
			if cog["name"] == name:
				return True, cog["folder"]
		return False, ''

	@commands.command()
	async def load(self, ctx, name):
		logger.info("[Administration load()] load command detected from "+str(ctx.message.author))
		if ctx.message.author in discord.utils.get(ctx.guild.roles, name="Bot_manager").members:
			logger.info("[Administration load()] "+str(ctx.message.author)+" successfully authenticated")
			valid, folder = self.validCog(name)
			if not valid:
				await ctx.send("```" + name + " isn't a real cog```")
				logger.info("[Administration load()] " + str(ctx.message.author) + " tried loading " + name + " which doesn't exist.")
				return
			try:
				self.bot.load_extension(folder + '.' + name)
				await ctx.send("{} command loaded.".format(name))
				logger.info("[Administration load()] " + name + " has been successfully loaded")
			except(AttributeError, ImportError) as e:
				await ctx.send("command load failed: {}, {}".format(type(e), str(e)))
				logger.info("[Administration load()] loading " + name + " failed :"+str(type(e)) +", "+ str(e))
		else:
			logger.info("[Administration load()] unauthorized command attempt detected from "+ str(ctx.message.author))
			await ctx.send("You do not have adequate permission to execute this command, incident will be reported")

	@commands.command()
	async def unload(self, ctx, name):
		logger.info("[Administration unload()] unload command detected from "+str(ctx.message.author))
		if ctx.message.author in discord.utils.get(ctx.guild.roles, name="Bot_manager").members:
			logger.info("[Administration unload()] "+str(ctx.message.author)+" successfully authenticated")
			valid, folder = self.validCog(name)
			if not valid:
				await ctx.send("```" + name + " isn't a real cog```")
				logger.info("[Administration load()] " + str(ctx.message.author) + " tried loading " + name + " which doesn't exist.")
				return

			self.bot.unload_extension(folder + '.' + name)
			await ctx.send("{} command unloaded".format(name))
			logger.info("[Administration unload()] " + name + " has been successfully loaded")
		else:
			logger.info("[Administration unload()] unauthorized command attempt detected from "+ ctx.message.author)
			await ctx.send("You do not have adequate permission to execute this command, incident will be reported")

	@commands.command()
	async def reload(self, ctx, name):
		logger.info("[Administration reload()] reload command detected from "+str(ctx.message.author))
		if ctx.message.author in discord.utils.get(ctx.guild.roles, name="Bot_manager").members:
			logger.info("[Administration reload()] "+str(ctx.message.author)+" successfully authenticated")
			valid, folder = self.validCog(name)
			if not valid:
				await ctx.send("```" + name + " isn't a real cog```")
				logger.info("[Administration load()] " + str(ctx.message.author) + " tried loading " + name + " which doesn't exist.")
				return

			self.bot.unload_extension(folder + '.' + name)
			try:
				self.bot.load_extension(folder + '.' + name)
				await ctx.send("`{} command reloaded`".format(folder + '.' + name))
				logger.info("[Administration reload()] "+name+" has been successfully reloaded")
			except(AttributeError, ImportError) as e:
				await ctx.send("Command load failed: {}, {}".format(type(e), str(e)))
				logger.info("[Administration load()] loading "+name+" failed :"+str(type(e)) +", "+ str(e))

		else:
			logger.info("[Administration reload()] unauthorized command attempt detected from "+ ctx.message.author)
			await ctx.send("You do not have adequate permission to execute this command, incident will be reported")

	@commands.command()
	async def exc(self, ctx, *args):
		logger.info("[Administration exc()] exc command detected from "+str(ctx.message.author) + "with arguments \""+" ".join(args)+"\"")
		if ctx.message.author in discord.utils.get(ctx.guild.roles, name="Bot_manager").members:
			logger.info("[Administration exc()] "+str(ctx.message.author)+" successfully authenticated")
			query = " ".join(args)
			#this got implemented for cases when the output of the command is too big to send to the channel
			exitCode, output = subprocess.getstatusoutput(query)
			prefix = "truncated output=\n"
			await send(ctx,"Exit Code: "+str(exitCode)+"\n```"+output+"```")
		else:
			logger.info("[Administration exc()] unauthorized command attempt detected from "+ str(ctx.message.author))
			await ctx.send("You do not have adequate permission to execute this command, incident will be reported")

	def get_column_headers_from_database(self):
		dbConn = self.connectToDatabase()
		dbCurr = dbConn.cursor()
		dbCurr.execute("Select * FROM commandstats LIMIT 0")
		colnames = [desc[0] for desc in dbCurr.description]
		dbCurr.close()
		dbConn.close()
		return [name.strip() for name in colnames]


	def determineXYFrequency(self,dbConn, filters=None):
		dbCurr = dbConn.cursor()
		logger.info("[Administration determineXYFrequency()] trying to create a dictionary from "+str(dbCurr)+" with the filters:\n\t"+str(filters))

		combinedFilter='", "'.join(str(e) for e in filters)
		combinedFilter="\""+combinedFilter+"\""
		sqlQuery="""select """+combinedFilter+""" from commandstats;"""
		logger.info("[Administration determineXYFrequency()] initial sql query to determine what entries needs to be created with the filter specified above:\n\t"+str(sqlQuery))
		dbCurr.execute(sqlQuery)

		#getting all the rows that need to be graphed
		results = dbCurr.fetchall()

		#where clause that will be used to determine what remaining rows still need to be added to the dictionary of results
		overarchingWHereClause=''

		#dictionary that will contain the stats that need to be graphed
		frequency = {}
		index=0

		#this loop will go through eachu unqiue entry that were turned from the results variable above to determine how much each unique entry
		# was appeared and needs that info added to frequency dictionary
		while len(results) > 0:
			logger.info("[Administration determineXYFrequency()] "+str(index)+"th index results of sql query=["+str(results[0])+"]")
			whereClause='' #where clause that keeps track of things that need to be added to the overarchingWhereClause
			entry=''
			for idx, val in enumerate(filters):
				if len(filters) == 1 + idx:
					entry+=str(results[0][idx])
					whereClause+="\""+str(val)+"\"='"+str(results[0][idx])+"'"
				else:
					entry+=str(results[0][idx])+'_'
					whereClause+="\""+str(val)+"\"='"+str(results[0][idx])+"' AND "
			logger.info("[Administration determineXYFrequency()] where clause for determining which entries match the entry ["+entry+"]:\n\t"+str(whereClause))
			sqlQuery="select "+combinedFilter+" from commandstats WHERE "+whereClause+";"
			logger.info("[Administration determineXYFrequency()] query that includes the above specified where clause for determining how many elements match the filter of ["+entry+"]:\n\t"+str(sqlQuery))
			dbCurr.execute(sqlQuery)
			resultsOfQueryForSpecificEntry=dbCurr.fetchall()
			frequency[entry]=len(resultsOfQueryForSpecificEntry)
			logger.info("[Administration determineXYFrequency()] determined that "+str(frequency[entry])+" entries exist for filter "+entry)

			if index > 0 :
				overarchingWHereClause+=' AND NOT ( '+whereClause+' )'
			else:
				overarchingWHereClause+=' NOT ( '+whereClause+' )'
			logger.info("[Administration determineXYFrequency()] updated where clause for discriminating against all entries that have already been recorded:\n\t"+str(overarchingWHereClause))
			sqlQuery="""select """+combinedFilter+""" from commandstats WHERE ( """+overarchingWHereClause+""" );"""
			logger.info("[Administration determineXYFrequency()] updated sql query to determine what remaining entries potentially need to be created after ruling out entries that match the where clause :\n\t"+str(sqlQuery))
			dbCurr.execute(sqlQuery)
			results = dbCurr.fetchall()
			index+=1
		dbCurr.close()
		dbConn.close()
		return frequency

	def connectToDatabase(self):
		try:
			host=None
			if 'localhost' == settings.ENVIRONMENT:
				host='127.0.0.1'
			else:
				host=settings.COMPOSE_PROJECT_NAME+'_wall_e_db'
			dbConnectionString="dbname='csss_discord_db' user='wall_e' host='"+host+"' password='"+settings.WALL_E_DB_PASSWORD+"'"
			logger.info("[Reminders __init__] dbConnectionString=[dbname='csss_discord_db' user='wall_e' host='"+host+"' password='******']")
			conn = psycopg2.connect(dbConnectionString)
			conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
			logger.info("[Reminders __init__] PostgreSQL connection established")
		except Exception as e:
			logger.error("[Reminders __init__] enountered following exception when setting up PostgreSQL connection\n{}".format(e))

		return conn

	@commands.command()
	async def frequency(self, ctx, *args):
		logger.info("[Administration frequency()] frequency command detected from "+str(ctx.message.author)+" with arguments ["+str(args)+"]")
		if len(args) == 0:
			await ctx.send("please specify which columns you want to count="+str(list(self.get_column_headers_from_database())))
			return
		else:
			dicResult = self.determineXYFrequency(self.connectToDatabase(), args)

		dicResult = sorted(dicResult.items(), key=lambda kv: kv[1])
		logger.info("[Administration frequency()] sorted dicResults by value")
		if len(dicResult) <= 50:
			logger.info("[Administration frequency()] dicResults's length is <= 50")
			labels = [i[0] for i in dicResult]
			numbers = [i[1] for i in dicResult]
			plt.rcdefaults()
			fig, ax = plt.subplots()
			y_pos = np.arange(len(labels))

			for i, v in enumerate(numbers):
				ax.text(v, i + .25, str(v), color='blue', fontweight='bold')

			ax.barh(y_pos, numbers, align='center',color='green')
			ax.set_yticks(y_pos)
			ax.set_yticklabels(labels)
			ax.invert_yaxis()  # labels read top-to-bottom

			if len(args) > 1:
				title='_'.join(str(arg) for arg in args[:len(args)-1])
				title+="_"+args[len(args)-1]
			else:
				title=args[0]

			ax.set_title("How may times each "+title+" appears in the database")
			fig.set_size_inches(18.5, 10.5)
			fig.savefig('image.png')
			logger.info("[Administration frequency()] graph created and saved")
			plt.close(fig)
			await ctx.send(file=discord.File('image.png'))
			logger.info("[Administration frequency()] graph image file has been sent")
		else:
			logger.info("[Administration frequency()] dicResults's length is > 50")
			numberOfPages = int(len(dicResult) / 50)
			if len(dicResult) % 50 != 0:
				numberOfPages+=1
			numOfBarsPerPage = int(len(dicResult) / numberOfPages )+1
			firstIndex, lastIndex= 0, numOfBarsPerPage-1
			msg=None
			currentPage=0


			while firstIndex < len(dicResult):
				logger.info("[Administration frequency()] creating a graph with entries "+str(firstIndex)+" to "+str(lastIndex))
				toReact = ['⏪', '⏩', '✅']


				labels = [i[0] for i in dicResult][firstIndex:lastIndex]
				numbers = [i[1] for i in dicResult][firstIndex:lastIndex]
				plt.rcdefaults()
				fig, ax = plt.subplots()
				y_pos = np.arange(len(labels))

				for i, v in enumerate(numbers):
					ax.text(v, i + .25, str(v), color='blue', fontweight='bold')

				ax.barh(y_pos, numbers, align='center',color='green')
				ax.set_yticks(y_pos)
				ax.set_yticklabels(labels)
				ax.invert_yaxis()  # labels read top-to-bottom
				ax.set_xlabel("Page "+str(currentPage)+"/"+str(numberOfPages-1))
				if len(args) > 1:
					title='_'.join(str(arg) for arg in args[:len(args)-1])
					title+="_"+args[len(args)-1]
				else:
					title=args[0]
				ax.set_title("How may times each "+title+" appears in the database")
				fig.set_size_inches(18.5, 10.5)
				fig.savefig('image.png')
				logger.info("[Administration frequency()] graph created and saved")
				plt.close(fig)
				if msg is None:
					msg = await ctx.send(file=discord.File('image.png'))
				else:
					await msg.delete()
					msg = await ctx.send(file=discord.File('image.png'))

				for reaction in toReact:
					await msg.add_reaction(reaction)
				def checkReaction(reaction, user):
					if not user.bot:  ##just making sure the bot doesnt take its own reactions
						##into consideration
						e = str(reaction.emoji)
						logger.info("[numOfBarsPerPage frequency()] reaction " + e + " detected from " + str(user))
						return e.startswith(('⏪', '⏩', '✅'))

				logger.info("[Administration frequency()] graph image file has been sent")

				userReacted = False
				while userReacted == False:
					try:
						userReacted = await self.bot.wait_for('reaction_add', timeout=20, check=checkReaction)
					except asyncio.TimeoutError:
						logger.info("[Administration frequency()] timed out waiting for the user's reaction.")

					if userReacted != False:
						if '⏪' == userReacted[0].emoji:
							firstIndex-=numOfBarsPerPage
							lastIndex-=numOfBarsPerPage
							currentPage-=1
							if firstIndex < 0:
								firstIndex, lastIndex= numOfBarsPerPage*3, numOfBarsPerPage*4
								currentPage=numberOfPages-1
							logger.info("[Administration frequency()] user indicates they want to go back to page " + str(currentPage))

						elif '⏩' == userReacted[0].emoji:
							firstIndex+=numOfBarsPerPage
							lastIndex+=numOfBarsPerPage
							currentPage+=1
							if firstIndex > len(dicResult):
								firstIndex, lastIndex= 0, numOfBarsPerPage
								currentPage=0
							logger.info("[Administration frequency()] user indicates they want to go to page " + str(currentPage))

						elif '✅' == userReacted[0].emoji:
							logger.info("[Administration frequency()] user indicates they are done with the roles command, deleting roles message")
							await msg.delete()
							return
					else:
						logger.info("[Administration frequency()] deleting message")
						await msg.delete()
						return

				logger.info("[Administration frequency()] updating firstIndex and lastIndex to "+str(firstIndex)+" and "+str(lastIndex)+" respectively")

def setup(bot):
	bot.add_cog(Administration(bot))
