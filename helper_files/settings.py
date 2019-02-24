# TODO: Come up with better name for this file
# Use this hold globals and other things need across the cogs
# that cannot be initialized for whatever reason in the cogs themselves

# To be initialed from main in the on_ready function
# Used in almost all the cogs for author name and author avatar in embeds
global BOT_NAME
BOT_NAME = ''
global BOT_AVATAR
BOT_AVATAR = ''

import os, json

##################################
## ENVIRONMENT VARIABLES TO USE ##
##################################

if 'ENVIRONMENT' not in os.environ:
	print("[main.py] No environment variable \"ENVIRONMENT\" seems to exist...read the README again")
	exit(1)
ENVIRONMENT = os.environ['ENVIRONMENT']
print("[main.py] variable \"ENVIRONMENT\" is set to \""+str(ENVIRONMENT)+"\"")

if 'TOKEN' not in os.environ:
	print("[main.py] No environment variable \"TOKEN\" seems to exist...read the README again")
	exit(1)
TOKEN = os.environ['TOKEN']   

print("[main.py] loading Wolfram Alpha API Environment Variable")
if 'WOLFRAMAPI' not in os.environ:
	print("[main.py] No environment variable \"WOLFRAMAPI\" seems to exist...read the README again")
	exit(1)
wolframAPI = os.environ['WOLFRAMAPI']

if 'WALL_E_DB_PASSWORD' not in os.environ:
	print("[main.py] No environment variable \"WALL_E_DB_PASSWORD\" seems to exist...read the README again")
	exit(1)

print("[main.py] loading Wolfram Alpha API Environment Variable")
if 'WALL_E_DB_PASSWORD' not in os.environ:
	print("[main.py] No environment variable \"WALL_E_DB_PASSWORD\" seems to exist...read the README again")
	exit(1)
WALL_E_DB_PASSWORD = os.environ['WALL_E_DB_PASSWORD']

if ENVIRONMENT != 'localhost':
	if 'COMPOSE_PROJECT_NAME' not in os.environ:
		print("[main.py] No environment variable \"COMPOSE_PROJECT_NAME\" seems to exist...read the README again")
		exit(1)

if ENVIRONMENT == 'localhost' or ENVIRONMENT == 'PRODUCTION':
	if 'BOT_LOG_CHANNEL_ID' not in os.environ:
		print("[main.py] No environment variable \"BOT_LOG_CHANNEL_ID\" seems to exist...read the README again")
		exit(1)
	else:
		BOT_LOG_CHANNEL = int(os.environ['BOT_LOG_CHANNEL_ID'])
	print("[main.py] variable \"BOT_LOG_CHANNEL\" is set to \""+str(BOT_LOG_CHANNEL)+"\"")

print('[main.py] loading cog names from json file')
with open('commands_to_load/cogs.json') as c:
	cogs = json.load(c)
cogs = cogs['cogs']