#!/usr/bin/env python

import argparse
import os
import platform
import subprocess
import sys
from enum import Enum
from pathlib import Path


def write_env_variables(basic_config__TOKEN, basic_config__GUILD_ID, basic_config__DOCKERIZED,
                        channel_names__BOT_GENERAL_CHANNEL, channel_names__MOD_CHANNEL,
                        channel_names__LEVELLING_CHANNEL, channel_names__EMBED_AVATAR_CHANNEL,
                        channel_names__INCIDENT_REPORT_CHANNEL, channel_names__LEVELLING_WEBSITE_AVATAR_IMAGE_CHANNEL,
                        channel_names__ANNOUNCEMENTS_CHANNEL, WALL_E_MODEL_PATH, database_config__WALL_E_DB_DBNAME,
                        database_config__WALL_E_DB_USER, database_config__WALL_E_DB_PASSWORD, database_config__ENABLED,
                        database_config__TYPE, COMPOSE_PROJECT_NAME, ORIGIN_IMAGE, POSTGRES_PASSWORD,
                        database_config__HOST, database_config__DB_PORT):
    with open("CI/user_scripts/wall_e.env", "r+") as f:
        f.seek(0)
        f.write(
            f"""ORIGIN_IMAGE='{ORIGIN_IMAGE}'

basic_config__TOKEN='{basic_config__TOKEN}'
basic_config__ENVIRONMENT='LOCALHOST'
basic_config__COMPOSE_PROJECT_NAME='{COMPOSE_PROJECT_NAME}'
basic_config__GUILD_ID='{basic_config__GUILD_ID}'
basic_config__DOCKERIZED='{basic_config__DOCKERIZED}'

channel_names__BOT_GENERAL_CHANNEL='{channel_names__BOT_GENERAL_CHANNEL}'
channel_names__MOD_CHANNEL='{channel_names__MOD_CHANNEL}'
channel_names__LEVELLING_CHANNEL='{channel_names__LEVELLING_CHANNEL}'
channel_names__EMBED_AVATAR_CHANNEL='{channel_names__EMBED_AVATAR_CHANNEL}'
channel_names__INCIDENT_REPORT_CHANNEL='{channel_names__INCIDENT_REPORT_CHANNEL}'
channel_names__LEVELLING_WEBSITE_AVATAR_IMAGE_CHANNEL='{channel_names__LEVELLING_WEBSITE_AVATAR_IMAGE_CHANNEL}'
channel_names__ANNOUNCEMENTS_CHANNEL='{channel_names__ANNOUNCEMENTS_CHANNEL}'

WALL_E_MODEL_PATH='{WALL_E_MODEL_PATH}'

database_config__ENABLED='{database_config__ENABLED}'
database_config__TYPE='{database_config__TYPE}'
database_config__HOST='{COMPOSE_PROJECT_NAME}_wall_e_db'
database_config__HOST='{database_config__HOST}'
database_config__DB_PORT='{database_config__DB_PORT}'
POSTGRES_PASSWORD='{POSTGRES_PASSWORD}'
database_config__WALL_E_DB_DBNAME='{database_config__WALL_E_DB_DBNAME}'
database_config__WALL_E_DB_USER='{database_config__WALL_E_DB_USER}'
database_config__WALL_E_DB_PASSWORD='{database_config__WALL_E_DB_PASSWORD}'
        """)


def not_in_venv():
    return sys.prefix == sys.base_prefix


parser = argparse.ArgumentParser(
    prog="Wall_e Runner",
    description="automates the process for running wall_e"
)

ENV_FILE_LOCATION = "./CI/user_scripts/wall_e.env"

parser.add_argument(
    "--skip_setup", action='store_true', default=False,
    help="intended to be used with --env_file flag so that the setup is not run though when the environment variables"
         " have already been pulled from the .env file"
)
parser.add_argument("--env_file",
                    action='store_true', default=False,
                    help=f"Indicator of whether to pull the environment variables from the file "
                         f"'{ENV_FILE_LOCATION}'. Helpful if the script has already been run and "
                         f"created the CI/user_scripts/wall_e.env file."
                    )
parser.add_argument("--overwrite_env_file", action='store_true',
                    help="indicator to the script that while you are pulling the env variables using --env_file, "
                         "you want to overwrite some of the imported variables")
parser.add_argument('--dockerized_wall_e', action='store', default=None,
                    choices=['true', 'false'],
                    help="indicates whether or not to run wall_e in a docker container. "
                         "Intended to be used if you are not also using the --skip_setup flag or are using the "
                         "--overwrite_env_file flag "
                    )
parser.add_argument('--database_type', action='store', default=None,
                    choices=['sqlite3', 'postgres'],
                    help="indicates whether you want to use sqlite3 or postgres for the database type."
                         "Intended to be used if you are not also using the --skip_setup flag or are using the"
                         " --overwrite_env_file flag "
                    )
parser.add_argument("--specify_wall_e_models_location", action='store', default=None,
                    help="used to specify the absolute path to the wall_e_models")
parser.add_argument("--launch_wall_e", action='store', default=None,
                    choices=['true', 'false'],
                    help="in set, script will tell you what command to run to run wall_e once this script sets up the"
                         " environment for you.")

args = parser.parse_args()
env_file_exists = os.path.exists(ENV_FILE_LOCATION) if args.env_file else False
overwrite_env_file = False

supported_os = platform.system() == "Linux"
basic_config__TOKEN = None
basic_config__ENVIRONMENT = 'LOCALHOST'
basic_config__COMPOSE_PROJECT_NAME = 'discord_bot'
basic_config__GUILD_ID = None

basic_config__DOCKERIZED = None

if args.dockerized_wall_e == 'true':
    basic_config__DOCKERIZED = 'y'
elif args.dockerized_wall_e == 'false':
    basic_config__DOCKERIZED = 'n'

channel_names__BOT_GENERAL_CHANNEL = 'bot-commands-and-misc'
channel_names__MOD_CHANNEL = 'council-summary'
channel_names__LEVELLING_CHANNEL = 'council'
channel_names__EMBED_AVATAR_CHANNEL = 'embed_avatars'
channel_names__INCIDENT_REPORT_CHANNEL = 'incident_reports'
channel_names__LEVELLING_WEBSITE_AVATAR_IMAGE_CHANNEL = 'leveling_website_avatar_images'
channel_names__ANNOUNCEMENTS_CHANNEL = 'announcements'

WALL_E_MODEL_PATH = args.specify_wall_e_models_location

database_config__WALL_E_DB_DBNAME = 'csss_discord_db'
database_config__WALL_E_DB_USER = 'wall_e'
database_config__WALL_E_DB_PASSWORD = 'wallEPassword'
database_config__ENABLED = True


class DatabaseType(Enum):
    sqlite3 = "sqlite3"
    postgreSQL = "postgreSQL"


database_config__TYPE = None
if args.database_type == DatabaseType.sqlite3.value:
    database_config__TYPE = DatabaseType.sqlite3.value
elif args.database_type == DatabaseType.postgreSQL.value:
    database_config__TYPE = DatabaseType.postgreSQL.value

database_config__HOST = None
database_config__DB_PORT = 5432
ORIGIN_IMAGE = 'sfucsssorg/wall_e'
POSTGRES_PASSWORD = 'postgres_passwd'

launch_wall_e = None
if args.launch_wall_e == 'true':
    launch_wall_e = 'y'
elif args.launch_wall_e == 'false':
    launch_wall_e = 'f'

env_file_is_specified = False
if env_file_exists:
    subprocess.getstatusoutput("python3 -m pip install python-dotenv")
    from dotenv import load_dotenv

    dotenv_path = Path(ENV_FILE_LOCATION)
    load_dotenv(dotenv_path=dotenv_path)
    overwrite_env_file = args.overwrite_env_file
    env_file_is_specified = True
go_through_setup = not args.skip_setup


def check_for_null_variables(**kwargs):
    for key, value in kwargs.items():
        if value is None:
            return True, key
    return False, None


def take_user_input(message, variable):
    if variable is not None:
        message += f" [or press s to skip and use the value of '{variable}']"
    message += "\n"
    user_input = input(message)
    return user_input if user_input != "s" else variable


def install_python_requirements():
    if not_in_venv():
        print("please active a python virtual environment before using this script")
        exit(0)
    print(subprocess.getstatusoutput(
        f"wget https://raw.githubusercontent.com/CSSS/wall_e_python_base/master/layer-1-requirements.txt && "
        f"wget https://raw.githubusercontent.com/CSSS/wall_e_python_base/master/layer-2-requirements.txt && "
        f"python3 -m pip install -r layer-1-requirements.txt && python3 -m pip install -r layer-2-requirements.txt && "
        f"rm layer-1-requirements.txt layer-2-requirements.txt && cd wall_e && "
        f"python3 -m pip install -r requirements.txt"
    )[1])


def recreate_database(database_type):
    if database_type == DatabaseType.sqlite3.value:
        print(subprocess.getstatusoutput("./recreate_sqlite3.sh")[1])
    if database_type == DatabaseType.postgreSQL.value:
        statusoutput = subprocess.getstatusoutput("dpkg -s postgresql-contrib &> /dev/null && echo $?")
        if statusoutput[0] == 1:
            raise Exception("please run 'sudo apt-get install postgresql-contrib' and then run this script again.")
        print(subprocess.getstatusoutput("./recreate_postgresql.sh")[1])


if go_through_setup or (env_file_is_specified and overwrite_env_file):
    basic_config__TOKEN = take_user_input(
        "What is your discord bot's token? [see https://discord.com/developers/docs/getting-started if "
        "you are not sure how to get it]", os.environ.get("basic_config__TOKEN", basic_config__TOKEN)
    )
    basic_config__GUILD_ID = take_user_input(
        "What is your discord guild's ID? [see https://discord.com/developers/docs/game-sdk/store and "
        "https://github.com/CSSS/wall_e/blob/master/documentation/Working_on_Bot/pictures/get_guild_id.png "
        "to see where to get it]", os.environ.get("basic_config__GUILD_ID", basic_config__GUILD_ID)
    )
    basic_config__DOCKERIZED = take_user_input(
        "Do you want to use a dockerized wall_e? [y/N] a dockerized wall_e is harder to debug but you might run"
        " into OS compatibility issues with some of the python modules",
        os.environ.get("basic_config__DOCKERIZED", basic_config__DOCKERIZED)
    ).lower()
    basic_config__DOCKERIZED = 1 if basic_config__DOCKERIZED == 'y' else 0
    if basic_config__DOCKERIZED == 0:
        database_config__TYPE = take_user_input(
            "Do you want to use db.sqlite3 for the database? [Y/n] [alternative is a separate service, "
            "dockerized or not]", os.environ.get("database_config__TYPE", database_config__TYPE)
        ).lower()
        database_config__TYPE = DatabaseType.sqlite3.value if database_config__TYPE == 'y' else DatabaseType.postgreSQL.value
    launch_wall_e = take_user_input(
        "Do you you want this script to launch wall_e? [Yn] [the alternative is to use PyCharm]", launch_wall_e
    ).lower()
    launch_wall_e = launch_wall_e == 'y'
    first_time = True
    while WALL_E_MODEL_PATH is None or not os.path.exists(WALL_E_MODEL_PATH):
        if not first_time:
            print(f"path {WALL_E_MODEL_PATH} does not exist")
        first_time = False
        WALL_E_MODEL_PATH = take_user_input(
            "Please specify the relative/absolute path for the wall_e_model",
            os.environ.get("WALL_E_MODEL_PATH", WALL_E_MODEL_PATH)
        )
    channel_names__BOT_GENERAL_CHANNEL = take_user_input(
        "What name do you want to set for the channel that the bot takes in the RoleCommands on? ",
        os.environ.get("channel_names__BOT_GENERAL_CHANNEL", channel_names__BOT_GENERAL_CHANNEL)
    )
    channel_names__MOD_CHANNEL = take_user_input(
        "What name do you want to set for the channel that bot sends ban related messages on? ",
        os.environ.get("channel_names__MOD_CHANNEL", channel_names__MOD_CHANNEL)
    )
    channel_names__LEVELLING_CHANNEL = take_user_input(
        "What name do you want to set for the channel that bot sends XP level related messages on? ",
        os.environ.get("channel_names__LEVELLING_CHANNEL", channel_names__LEVELLING_CHANNEL)
    )
    channel_names__ANNOUNCEMENTS_CHANNEL = take_user_input(
        "What name do you want to set for the channel that announcements are sent on? ",
        os.environ.get("channel_names__ANNOUNCEMENTS_CHANNEL", channel_names__ANNOUNCEMENTS_CHANNEL)
    )
    channel_names__EMBED_AVATAR_CHANNEL = take_user_input(
        "What name do you want to set for the channel where embed avatars are stored? ",
        os.environ.get("channel_names__EMBED_AVATAR_CHANNEL", channel_names__EMBED_AVATAR_CHANNEL)
    )
    channel_names__INCIDENT_REPORT_CHANNEL = take_user_input(
        "What name do you want to set for the channel where incident reports are sent? ",
        os.environ.get("channel_names__INCIDENT_REPORT_CHANNEL", channel_names__INCIDENT_REPORT_CHANNEL)
    )
    channel_names__LEVELLING_WEBSITE_AVATAR_IMAGE_CHANNEL = take_user_input(
        "What name do you want to set for the channel where the images used on the levelling website are sent? ",
        os.environ.get(
            "channel_names__LEVELLING_WEBSITE_AVATAR_IMAGE_CHANNEL",
            channel_names__LEVELLING_WEBSITE_AVATAR_IMAGE_CHANNEL
        )
    )

elif env_file_is_specified:
    basic_config__TOKEN = os.environ.get("basic_config__TOKEN", None)
    if basic_config__TOKEN is None:
        basic_config__TOKEN = take_user_input(
            "What is your discord bot's token? [see https://discord.com/developers/docs/getting-started if "
            "you are not sure how to get it]", basic_config__TOKEN
        )
    basic_config__GUILD_ID = os.environ.get("basic_config__GUILD_ID", None)
    if basic_config__GUILD_ID is None:
        basic_config__GUILD_ID = take_user_input(
            "What is your discord guild's ID? [see https://discord.com/developers/docs/game-sdk/store and "
            "https://github.com/CSSS/wall_e/blob/master/documentation/Working_on_Bot/pictures/get_guild_id.png "
            "to see where to get it]", basic_config__GUILD_ID
        )
    basic_config__DOCKERIZED = os.environ.get("basic_config__DOCKERIZED", None)
    if basic_config__DOCKERIZED is None:
        basic_config__DOCKERIZED = take_user_input(
            "Do you want to use a dockerized wall_e? [y/N] a dockerized wall_e is harder to debug but you might run"
            " into OS compatibility issues with some of the python modules",
            basic_config__DOCKERIZED
        ).lower()
    basic_config__DOCKERIZED = 1 if basic_config__DOCKERIZED == 'y' else 0
    if basic_config__DOCKERIZED == 0:
        database_config__TYPE = os.environ.get("database_config__TYPE", None)
        if database_config__TYPE is None:
            database_config__TYPE = take_user_input(
                "Do you want to use db.sqlite3 for the database? [Y/n] [alternative is a separate service, "
                "dockerized or not]", database_config__TYPE
            ).lower()
            database_config__TYPE = DatabaseType.sqlite3.value if database_config__TYPE == 'y' else DatabaseType.postgreSQL.value
    if launch_wall_e is None:
        launch_wall_e = take_user_input(
            "Do you you want this script to launch wall_e? [Yn] [the alternative is to use PyCharm]", launch_wall_e
        ).lower()
    launch_wall_e = launch_wall_e == 'y'
    first_time = True
    WALL_E_MODEL_PATH = os.environ.get("WALL_E_MODEL_PATH", None)
    while WALL_E_MODEL_PATH is None or not os.path.exists(WALL_E_MODEL_PATH):
        if not first_time:
            print(f"path {WALL_E_MODEL_PATH} does not exist")
        first_time = False
        WALL_E_MODEL_PATH = take_user_input(
            "Please specify the relative/absolute path for the wall_e_model",
            WALL_E_MODEL_PATH
        )
    channel_names__BOT_GENERAL_CHANNEL = os.environ.get("channel_names__BOT_GENERAL_CHANNEL", None)
    if channel_names__BOT_GENERAL_CHANNEL is None:
        channel_names__BOT_GENERAL_CHANNEL = take_user_input(
            "What name do you want to set for the channel that the bot takes in the RoleCommands on? ",
            channel_names__BOT_GENERAL_CHANNEL
        )

    channel_names__MOD_CHANNEL = os.environ.get("channel_names__MOD_CHANNEL", None)
    if channel_names__MOD_CHANNEL is None:
        channel_names__MOD_CHANNEL = take_user_input(
            "What name do you want to set for the channel that bot sends ban related messages on? ",
            channel_names__MOD_CHANNEL
        )
    channel_names__LEVELLING_CHANNEL = os.environ.get("channel_names__LEVELLING_CHANNEL", None)
    if channel_names__LEVELLING_CHANNEL is None:
        channel_names__LEVELLING_CHANNEL = take_user_input(
            "What name do you want to set for the channel that bot sends XP level related messages on? ",
            channel_names__LEVELLING_CHANNEL
        )
    channel_names__ANNOUNCEMENTS_CHANNEL = os.environ.get("channel_names__ANNOUNCEMENTS_CHANNEL", None)
    if channel_names__ANNOUNCEMENTS_CHANNEL is None:
        channel_names__ANNOUNCEMENTS_CHANNEL = take_user_input(
            "What name do you want to set for the channel that announcements are sent on? ",
            channel_names__ANNOUNCEMENTS_CHANNEL
        )
    channel_names__EMBED_AVATAR_CHANNEL = os.environ.get("channel_names__EMBED_AVATAR_CHANNEL", None)
    if channel_names__EMBED_AVATAR_CHANNEL is None:
        channel_names__EMBED_AVATAR_CHANNEL = take_user_input(
            "What name do you want to set for the channel where embed avatars are stored? ",
            channel_names__EMBED_AVATAR_CHANNEL
        )
    channel_names__INCIDENT_REPORT_CHANNEL = os.environ.get("channel_names__INCIDENT_REPORT_CHANNEL", None)
    if channel_names__INCIDENT_REPORT_CHANNEL is None:
        channel_names__INCIDENT_REPORT_CHANNEL = take_user_input(
            "What name do you want to set for the channel where incident reports are sent? ",
            channel_names__INCIDENT_REPORT_CHANNEL

        )
    channel_names__LEVELLING_WEBSITE_AVATAR_IMAGE_CHANNEL = os.environ.get(
        "channel_names__LEVELLING_WEBSITE_AVATAR_IMAGE_CHANNEL", None
    )
    channel_names__LEVELLING_WEBSITE_AVATAR_IMAGE_CHANNEL = take_user_input(
        "What name do you want to set for the channel where the images used on the levelling website are sent? ",
        os.environ.get(
            "channel_names__LEVELLING_WEBSITE_AVATAR_IMAGE_CHANNEL",
            channel_names__LEVELLING_WEBSITE_AVATAR_IMAGE_CHANNEL
        )
    )

if database_config__TYPE != DatabaseType.postgreSQL.value and database_config__TYPE != DatabaseType.sqlite3.value:
    print(f"unrecognized database type of {database_config__TYPE} detected")
    exit(1)
if (basic_config__DOCKERIZED == 1 or database_config__TYPE == DatabaseType.postgreSQL.value) and not supported_os:
    print(
        "sorry, script is currently not setup to use anything other than dockerized postgres database on "
        "non-linux systems :-(")
    print("Feel free to add that feature in")
    exit(1)


essential_variables_are_null = check_for_null_variables(
    basic_config__TOKEN=basic_config__TOKEN, basic_config__GUILD_ID=basic_config__GUILD_ID,
    basic_config__DOCKERIZED=basic_config__DOCKERIZED, WALL_E_MODEL_PATH=WALL_E_MODEL_PATH
)
if essential_variables_are_null[0]:
    raise Exception(f"necessary variable {essential_variables_are_null[1]} is None")

write_env_variables(
    basic_config__TOKEN, basic_config__GUILD_ID, basic_config__DOCKERIZED, channel_names__BOT_GENERAL_CHANNEL,
    channel_names__MOD_CHANNEL, channel_names__LEVELLING_CHANNEL, channel_names__EMBED_AVATAR_CHANNEL,
    channel_names__INCIDENT_REPORT_CHANNEL, channel_names__LEVELLING_WEBSITE_AVATAR_IMAGE_CHANNEL,
    channel_names__ANNOUNCEMENTS_CHANNEL, WALL_E_MODEL_PATH, database_config__WALL_E_DB_DBNAME,
    database_config__WALL_E_DB_USER, database_config__WALL_E_DB_PASSWORD, database_config__ENABLED,
    database_config__TYPE, basic_config__COMPOSE_PROJECT_NAME, ORIGIN_IMAGE,POSTGRES_PASSWORD, database_config__HOST,
    database_config__DB_PORT)


if basic_config__DOCKERIZED == 1:
    COMPOSE_PROJECT_NAME = basic_config__COMPOSE_PROJECT_NAME

    database_config__TYPE = DatabaseType.postgreSQL.value
    database_config__HOST = f"{basic_config__COMPOSE_PROJECT_NAME}_wall_e_db"
    ORIGIN_IMAGE = 'sfucsssorg/walle'
    POSTGRES_PASSWORD = POSTGRES_PASSWORD
    subprocess.getstatusoutput(
        f"./CI/user_scripts/set_env.sh && "
        f"./CI/user_scripts/set-dev-env.sh && "
        f"docker logs -f {basic_config__COMPOSE_PROJECT_NAME}_wall_e"
    )
else:
    if database_config__TYPE == DatabaseType.postgreSQL.value:
        database_config__HOST = "127.0.0.1"
        database_config__DB_PORT = 5432
    else:
        database_config__HOST = 'discord_bot_wall_e_db'
    install_python_requirements()
    recreate_database(database_config__TYPE)


if launch_wall_e:
    print("if you want to run wall_e, run:\n. ./CI/user_scripts/set_env.sh && pushd wall_e && python3 main.py")