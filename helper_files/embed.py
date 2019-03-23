import discord
import asyncio
import json

from discord.ext import commands

def embed(title='', content='', description='', author='', colour=0x00bfbd, link='', thumbnail='', avatar='', footer=''):
	"""
	title:<str> Title of the embed 99% of the time it'll be the command name, exceptions when it makes sense like with the sfu command.\n
	content:<array[tuples]> Array of tuples. Tuple per field of the embed. Field name at index 0 and value at index 1. \n
	description:<str> Appears under the title. \n
	author:<str> Used to indicate user who involked the command or the bot itself when it makes sense like with the echo command.\n
	colour:<0x......> Used to set the coloured strip on the left side of the embed, by default set to a nice blue colour.\n
	link: <deprecated>\n
	thumbnail:<str> Url to image to be used in the embed. Thumbnail appears top right corner of the embed.\n
	avatar:<str> Used to set avatar next to author's name. Must be url. \n
	footer:<str> Used for whatever."""

	#these are put in place cause of the limits on embed described here
	# https://discordapp.com/developers/docs/resources/channel#embed-limits
	if len(title) > 256:
		ctx.send("length of the title ["+str(title)+"] being added to the name field is "+str(len(title)-256)+" too big, pleae cut down to a size of 256")
		logger.info("[Mod embed()] length of name ["+str(title)+"] being added to the field is too big")
		return False

	if len(description) > 2048:
		ctx.send("length of name ["+str(description)+"] being added to the name field is "+str(len(description)-2048)+" too big, pleae cut down to a size of 2048")
		logger.info("[Mod embed()] length of name ["+str(description)+"] being added to the field is too big")
		return False

	if len(contents) > 25:
		ctx.send("length of name ["+str(contents)+"] being added to the name field is "+str(contents.length()-25)+" too big, pleae cut down to a size of 25")
		logger.info("[Mod embed()] length of name ["+str(contents)+"] being added to the field is too big")
		return False

	for record in content:
		if len(record[0]) > 256:
			ctx.send("length of name ["+str(record[0])+"] being added to the name field is "+str(len(record[0])-256)+" too big, pleae cut down to a size of 256")
			logger.info("[Mod embed()] length of name ["+str(record[0])+"] being added to the field is too big")
			return False
		if len(record[1]) > 1024:
			ctx.send("length of name ["+str(record[1])+"] being added to the name field is "+str(len(record[1])-1024)+" too big, pleae cut down to a size of 1024")
			logger.info("[Mod embed()] length of name ["+str(record[1])+"] being added to the field is too big")
			return False

	if len(footer) > 2048:
		ctx.send("length of name ["+str(footer)+"] being added to the name field is "+str(len(footer)-2048)+" too big, pleae cut down to a size of 2048")
		logger.info("[Mod embed()] length of name ["+str(footer)+"] being added to the field is too big")
		return False

	embObj = discord.Embed(title=title, type='rich')
	embObj.description = description
	embObj.set_author(name=author, icon_url=avatar)
	embObj.colour = colour
	embObj.set_thumbnail(url=thumbnail)
	embObj.set_footer(text=footer)
	#embObj.url = link
	#parse content to add fields
	for x in content:
		embObj.add_field(name=x[0], value=x[1], inline=False)
	return embObj