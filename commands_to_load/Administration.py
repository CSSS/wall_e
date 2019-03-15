from discord.ext import commands
import discord
import subprocess
import helper_files.settings as settings
import csv
import logging
import matplotlib.pyplot as plt
import numpy as np
import operator

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
			if len(output)>2000 :
				logger.info("getting reduced")
				length = len(output)- (len(output) - 2000) #taking length of just output into account
				length = length - len(prefix) #taking length of prefix into account
				length = length - 6 #taking length of prefix into account
				length = length - 12 - len(str(exitCode)) #taking exit code info into account
				output=output[:length]
				await ctx.send("Exit Code: "+str(exitCode)+"\n"+prefix+"```"+output+"```")
			elif len(output) == 0:
				await ctx.send("Exit Code: "+str(exitCode)+"\n")
			else:
				await ctx.send("Exit Code: "+str(exitCode)+"\n```"+output+"```")
		else:
			logger.info("[Administration exc()] unauthorized command attempt detected from "+ str(ctx.message.author))
			await ctx.send("You do not have adequate permission to execute this command, incident will be reported")

	def get_column_headers(self):
		csvFile = csv.DictReader(open('logs/stats_of_commands.csv', 'r'))
		return [name.lower().strip().replace(' ', '_') for name in csvFile.fieldnames]

	def getCSVFILE(self):
		csvFile = csv.DictReader(open('logs/stats_of_commands.csv', 'r'))
		csvFile.fieldnames = [name.lower().strip().replace(' ', '_') for name in csvFile.fieldnames]
		dict_list = []
		for line in csvFile:
			out_dict={}
			for k, v in line.items():
				out_dict[k]=v.strip()
			if "Direct Message with " not in str(out_dict.values()):
				dict_list.append(out_dict)
		return dict_list

	def CommandFrequency(self,csv, filters=None):
		logger.info("[Administration CommandFrequency()] trying to create a dictionary from "+str(csv)+" with the filters "+str(filters))
		channels = {}
		for line in csv:
			entry = line[filters[0]]
			for theFilter in filters[1:]:
				entry+="_"+line[theFilter]
			logger.info("[Administration CommandFrequency()] entry "+str(entry)+" found in csv" )				
			if entry not in channels:
				logger.info("[Administration CommandFrequency()] entry "+str(entry)+" was not in dictionary, initializing it" )				
				channels[entry]=1
			else:
				logger.info("[Administration CommandFrequency()] entry "+str(entry)+" in dictionary is being incremented to "+str(channels[entry]) )				
				channels[entry]+=1
		return channels

	@commands.command()
	async def frequency(self, ctx, *args):
		logger.info("[Administration frequency()] frequency command detected from "+str(ctx.message.author)+" with arguments ["+str(args)+"]")
		if len(args) == 0:
			await ctx.send("please specify which columns you want to count="+str(list(self.get_column_headers())))
		else:
			dicResult = self.CommandFrequency(self.getCSVFILE(), args)

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
			#ax.set_xlabel(x_label)
			#ax.set_title(title)
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
			firstIndex, lastIndex= 0, numOfBarsPerPage
			while firstIndex < len(dicResult):
				logger.info("[Administration frequency()] creating a graph with entries "+str(firstIndex)+" to "+str(lastIndex))
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
				#ax.set_xlabel(x_label)
				#ax.set_title(title)
				fig.set_size_inches(18.5, 10.5)
				fig.savefig('image.png')
				logger.info("[Administration frequency()] graph created and saved")
				plt.close(fig)
				await ctx.send(file=discord.File('image.png'))
				logger.info("[Administration frequency()] graph image file has been sent")
				firstIndex+=numOfBarsPerPage
				lastIndex+=numOfBarsPerPage
				logger.info("[Administration frequency()] updating firstIndex and lastIndex to "+str(firstIndex)+" to "+str(lastIndex)+" respectively")


def setup(bot):
	bot.add_cog(Administration(bot))
