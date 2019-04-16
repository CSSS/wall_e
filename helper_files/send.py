

async def send(ctx, content=None, tts=False, embed=None, file=None, files=None, delete_after=None, nonce=None):

	# done because discord has a character limit of 2000 for each message
	# so what basically happens is it first tries to send the full message, then if it cant, it breaks it down into 2000 sizes messages and send them individually
	try:
		await ctx.send(content)
	except (aiohttp.ClientError, discord.errors.HTTPException) as exc:
		finished = False
		firstIndex, lastIndex = 0, 2000
		first = True
		while not finished:
			if first:
				first=False
				await ctx.send(output[firstIndex:lastIndex], tts=tts,embed=embed,file=file,files=files,delete_after=delete_after, nonce=nonce)
			else:
				await ctx.send(output[firstIndex:lastIndex], tts=tts, delete_after=delete_after, nonce=nonce)

			firstIndex = lastIndex
			lastIndex += 2000
			if len(output[firstIndex:lastIndex]) == 0:
				finished = True
	except Exception as e:
		exc_str = '{}: {}'.format(type(exc).__name__, exc)
		logger.error('[main.py send()] write to channel failed\n{}'.format(exc_str))
