#from discord.ext import commands
import discord
import asyncio
import logging

logger = logging.getLogger('wall_e')
from main import BOT_USER_ID
async def paginateEmbed(bot, ctx, listToEmbed, numOfPages=0, numOfPageEntries=0, title=" "):
	logger.info("[Paginate paginateEmbed()] called with following argument: listToEmbed="+str(listToEmbed)+"\n\tnumOfPages="+str(numOfPages)+", numOfPageEntries="+str(numOfPageEntries)+" and title="+title)
	if numOfPages == 0:
		if numOfPageEntries == 0:
			logger.error("[Paginate paginateEmbed()] you need to specify either \"numOfPages\" or \"numOfPageEntries\"")
			return
		else:
			if int(len(listToEmbed)/numOfPageEntries) == len(listToEmbed)/numOfPageEntries:
				numOfPages = int(len(listToEmbed)/numOfPageEntries)
			else:
				numOfPages = int(len(listToEmbed)/numOfPageEntries)+1
			
	else:
		if numOfPageEntries != 0:
			logger.error("[Paginate paginateEmbed()] you specified both \"numOfPages\" and \"numOfPageEntries\", please only use one")
		else:
			if int(len(listToEmbed)/numOfPages) == len(listToEmbed)/numOfPages:
				numOfPageEntries = int(len(listToEmbed)/numOfPages)
			else:
				numOfPageEntries = int(len(listToEmbed)/numOfPages)+1
	logger.info("[Paginate paginateEmbed()] numOfPageEntries set to "+str(numOfPageEntries)+", numOfPages set to "+str(numOfPages)+" and number of total entries is "+str(len(listToEmbed))+".")
	listOfRoles = [[["" for z in range(2)]  for x in range(numOfPageEntries)] for y in range(numOfPages)]

	x, y = 0, 0; 
	for roles in listToEmbed:
		listOfRoles[y][x][0]=roles[0]
		listOfRoles[y][x][1]=roles[1]
		x+=1
		if x == numOfPageEntries:
			y+=1
			x=0
	logger.info("[Paginate paginateEmbed()] listToEmbed added to roles matrix for pagination")
	currentPage=0
	firstRun=True
	msg=None

	while True:
			logger.info("[Paginate paginateEmbed()] loading page "+str(currentPage)+" with roles "+str(listOfRoles[currentPage]))
			embed=discord.Embed(title=title, color=0x81e28d)
			for x in listOfRoles[currentPage]:
				if x[0] != "":
					embed.add_field(name=x[0],value=x[1],inline=False)
			embed.set_footer(text='{}/{}'.format(str(currentPage+1),str(numOfPages)))
			logger.info("[Paginate paginateEmbed()] embed succesfully created and populated for page "+str(currentPage))
			
			#determining which reactions are needed
			if currentPage == 0:
				toReact = ['⏩', '✅']
			elif currentPage == numOfPages - 1:
				toReact = ['⏪', '✅']
			else:
				toReact = ['⏪', '⏩', '✅']

			#setting the content if it was the first run through or not.
			if firstRun == True:
				firstRun = False
				msg = await ctx.send(content=None,embed=embed)
				logger.info("[Paginate paginateEmbed()] sent message")
			else:
				await msg.edit(embed=embed)
				await msg.clear_reactions()
				logger.info("[Paginate paginateEmbed()] edited message")

			   #adding reactions deemed necessary to page
			for reaction in toReact:
				await msg.add_reaction(reaction)

			logger.info("[Paginate paginateEmbed()] added all reactions to message")
			def checkReaction(reaction, user):
				if user.id != BOT_USER_ID: ##just making sure the bot doesnt take its own reactions
				##into consideration
					e = str(reaction.emoji)
					logger.info("[Paginate paginateEmbed()] reaction "+e+" detected from "+str(user))
					return e.startswith(('⏪', '⏩', '✅'))

			userReacted=False
			while userReacted == False:
				try:
					userReacted = await bot.wait_for('reaction_add',timeout=20, check=checkReaction)
				except asyncio.TimeoutError:
					logger.info("[Paginate paginateEmbed()] timed out waiting for the user's reaction.")

				if userReacted != False:
					if '⏪' ==  userReacted[0].emoji:
						logger.info("[Paginate paginateEmbed()] user indicates they want to go back a page from "+str(currentPage)+" to "+str(currentPage-1))
						currentPage=currentPage-1
					elif  '⏩' == userReacted[0].emoji:
						logger.info("[Paginate paginateEmbed()] user indicates they want to go forward a page from "+str(currentPage)+" to "+str(currentPage+1))
						currentPage=currentPage+1
					elif  '✅' == userReacted[0].emoji:
						logger.info("[Paginate paginateEmbed()] user indicates they are done with the roles command, deleting roles message")
						await msg.delete()
						return
				else:
					logger.info("[Paginate paginateEmbed()] deleting message")
					await msg.delete()
					return

async def paginate(bot, ctx, listToPaginate, numOfPages=0, numOfPageEntries=0, title=" "):
	logger.info("[Paginate paginate()] added roles to rolesList and sorted them alphabetically")
	if numOfPages == 0:
		if numOfPageEntries == 0:
			logger.error("[Paginate paginate()] you need to specify either \"numOfPages\" or \"numOfPageEntries\"")
			return
		else:
			if int(len(listToPaginate)/numOfPageEntries) == len(listToPaginate)/numOfPageEntries:
				numOfPages = int(len(listToPaginate)/numOfPageEntries)
			else:
				numOfPages = int(len(listToPaginate)/numOfPageEntries)+1
	else:
		if numOfPageEntries != 0:
			logger.error("[Paginate paginate()] you specified both \"numOfPages\" and \"numOfPageEntries\", please only use one")
		else:
			if int(len(listToPaginate)/numOfPages) == len(listToPaginate)/numOfPages:
				numOfPageEntries = int(len(listToPaginate)/numOfPages)
			else:
				umOfPageEntries = int(len(listToPaginate)/numOfPages)+1

	logger.info("[Paginate paginate()] numOfPageEntries set to "+str(numOfPageEntries)+" and numOfPages set to "+str(numOfPages))
	listOfRoles = [[["" for z in range(len(listToPaginate[0]))]  for x in range(numOfPageEntries)] for y in range(numOfPages)]
	x, y = 0, 0;
	for roles in listToPaginate:
		listOfRoles[y][x]=roles
		x+=1
		if x == numOfPageEntries:
			y+=1
			x=0
	logger.info("[Paginate paginate()] list added to roles matrix for pagination")
	currentPage=0
	firstRun=True
	msg=None
	while True:
			logger.info("[Paginate paginate()] loading page "+str(currentPage)+" with roles "+str(listOfRoles))
			output=title+"\n\n```"
			for x in listOfRoles[currentPage]:
				if x != 0:
					output+='\t\"'+str(x)+"\"\n"
			output+='```{}/{}'.format(str(currentPage+1),str(numOfPages))
			logger.info("[Paginate paginate()] created and filled Embed with roles of the current page "+str(currentPage))
			if currentPage == 0:
				toReact = ['⏩', '✅']
			elif currentPage == numOfPages - 1:
				toReact = ['⏪', '✅']
			else:
				toReact = ['⏪', '⏩', '✅']

			if firstRun == True:
				firstRun = False
				msg = await ctx.send(output)
				logger.info("[Paginate paginate()] sent message")
			else:
				await msg.delete()
				msg = await ctx.send(output)
				logger.info("[Paginate paginate()] sent updated message with the next page of roles")
			for reaction in toReact:
				await msg.add_reaction(reaction)

			logger.info("[Paginate paginate()] added all reactions to message")
			def checkReaction(reaction, user):
				if user.id != BOT_USER_ID:
					e = str(reaction.emoji)
					logger.info("[Paginate paginate()] user reaction detected..."+ str(e))
					return e.startswith(('⏪', '⏩', '✅'))

			userReacted=False
			while userReacted == False:
				try:
					userReacted = await bot.wait_for('reaction_add',timeout=20, check=checkReaction)
				except asyncio.TimeoutError:
					logger.info("[Paginate paginate()] timed out waiting for the user's reaction.")

				if userReacted != False:
					if '⏪' ==  userReacted[0].emoji:
						logger.info("[Paginate paginate()] user indicates they want to go back a page from"+str(currentPage)+" to "+str(currentPage-1))
						currentPage=currentPage-1
					elif  '⏩' == userReacted[0].emoji:
						logger.info("[Paginate paginate()] user indicates they want to go forward a page from"+str(currentPage)+" to "+str(currentPage+1))
						currentPage=currentPage+1
					elif  '✅' == userReacted[0].emoji:
						logger.info("[Paginate paginate()] user indicates they are done with the roles command, deleting roles message")
						await msg.delete()
						return
				else:
					logger.info("[Paginate paginate()] deleting message")
					await msg.delete()
					return