# hold all variables that are needed across the cogs

import json
import os

# To be initialed from main in the on_ready function
# Used in almost all the cogs for author name and author avatar in embeds
BOT_NAME = ''
BOT_AVATAR = ''

#################################
# ENVIRONMENT VARIABLES TO USE ##
#################################

if 'ENVIRONMENT' not in os.environ:
    print("[settings.py] No environment variable \"ENVIRONMENT\" seems to exist...read the README again")
    exit(1)
ENVIRONMENT = os.environ['ENVIRONMENT']
print("[settings.py] variable \"ENVIRONMENT\" is set to \""+str(ENVIRONMENT)+"\"")

if 'TOKEN' not in os.environ:
    print("[settings.py] No environment variable \"TOKEN\" seems to exist...read the README again")
    exit(1)
TOKEN = os.environ['TOKEN']
os.environ['TOKEN'] = ''
print("[settings.py] variable \"TOKEN\" has been set")

if 'WOLFRAMAPI' not in os.environ:
    print("[settings.py] No environment variable \"WOLFRAMAPI\" seems to exist...read the README again")
    exit(1)
wolframAPI = os.environ['WOLFRAMAPI']
os.environ['WOLFRAMAPI'] = ''
print("[settings.py] variable \"WOLFRAMAPI\" has been set")

if ENVIRONMENT != 'localhost_noDB':
    if 'POSTGRES_DB_USER' not in os.environ:
        print("[settings.py] No environment variable \"POSTGRES_DB_USER\" seems to exist...read the README again")
        exit(1)
    POSTGRES_DB_USER = os.environ['POSTGRES_DB_USER']
    print("[settings.py] variable \"POSTGRES_DB_USER\" is set to \""+str(POSTGRES_DB_USER)+"\"")

    if 'POSTGRES_DB_DBNAME' not in os.environ:
        print("[settings.py] No environment variable \"POSTGRES_DB_DBNAME\" seems to exist...read the README again")
        exit(1)
    POSTGRES_DB_DBNAME = os.environ['POSTGRES_DB_DBNAME']
    print("[settings.py] variable \"POSTGRES_DB_DBNAME\" is set to \""+str(POSTGRES_DB_DBNAME)+"\"")

    if 'POSTGRES_PASSWORD' not in os.environ:
        print("[settings.py] No environment variable \"POSTGRES_PASSWORD\" seems to exist...read the README again")
        exit(1)
    POSTGRES_PASSWORD = os.environ['POSTGRES_PASSWORD']
    os.environ['POSTGRES_PASSWORD'] = ''
    print("[settings.py] variable \"POSTGRES_PASSWORD\" has been set.")

    if 'WALL_E_DB_USER' not in os.environ:
        print("[settings.py] No environment variable \"WALL_E_DB_USER\" seems to exist...read the README again")
        exit(1)
    WALL_E_DB_USER = os.environ['WALL_E_DB_USER']
    print("[settings.py] variable \"WALL_E_DB_USER\" is set to \""+str(WALL_E_DB_USER)+"\"")

    if 'WALL_E_DB_DBNAME' not in os.environ:
        print("[settings.py] No environment variable \"WALL_E_DB_DBNAME\" seems to exist...read the README again")
        exit(1)
    WALL_E_DB_DBNAME = os.environ['WALL_E_DB_DBNAME']
    print("[settings.py] variable \"WALL_E_DB_DBNAME\" is set to \""+str(WALL_E_DB_DBNAME)+"\"")

    if 'WALL_E_DB_PASSWORD' not in os.environ:
        print("[settings.py] No environment variable \"WALL_E_DB_PASSWORD\" seems to exist...read the README again")
        exit(1)
    WALL_E_DB_PASSWORD = os.environ['WALL_E_DB_PASSWORD']
    os.environ['WALL_E_DB_PASSWORD'] = ''
    print("[settings.py] variable \"WALL_E_DB_PASSWORD\" has been set.")


if ENVIRONMENT != 'localhost' and ENVIRONMENT != 'localhost_noDB':
    if 'COMPOSE_PROJECT_NAME' not in os.environ:
        print("[settings.py] No environment variable \"COMPOSE_PROJECT_NAME\" seems to exist...read the README again")
        exit(1)
    COMPOSE_PROJECT_NAME = os.environ['COMPOSE_PROJECT_NAME']
    print("[settings.py] variable \"COMPOSE_PROJECT_NAME\" is set to \""+str(COMPOSE_PROJECT_NAME)+"\"")

if ENVIRONMENT == 'PRODUCTION':
    if 'BOT_LOG_CHANNEL_ID' not in os.environ:
        print("[settings.py] No environment variable \"BOT_LOG_CHANNEL_ID\" seems to exist...read the README again")
        exit(1)
    else:
        BOT_LOG_CHANNEL = int(os.environ['BOT_LOG_CHANNEL_ID'])
    print("[settings.py] variable \"BOT_LOG_CHANNEL\" is set to \""+str(BOT_LOG_CHANNEL)+"\"")

if ENVIRONMENT == 'TEST':
    if 'BRANCH_NAME' not in os.environ:
        print("[settings.py] No environment variable \"BRANCH_NAME\" seems to exist...read the README again")
        exit(1)
    BRANCH_NAME = os.environ['BRANCH_NAME']
    print("[settings.py] variable \"BRANCH_NAME\" is set to \""+str(BRANCH_NAME)+"\"")

print('[settings.py] loading cog names from json file')
with open('commands_to_load/cogs.json') as c:
    cogs = json.load(c)
cogs = cogs['cogs']
