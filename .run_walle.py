#!/usr/bin/env python

import argparse
import os
import platform
import subprocess
from enum import Enum
from pathlib import Path


ENV_FILE_LOCATION = "./CI/validate_and_deploy/2_deploy/user_scripts/wall_e.env"
RUN_ENV_FILE_LOCATION = "./CI/validate_and_deploy/2_deploy/user_scripts/run_wall_e.env"


class DatabaseType(Enum):
    sqlite3 = "sqlite3"
    postgreSQL = "postgreSQL"


def create_argument_parser():
    """

    :return: an argparser
    """
    parser_obj = argparse.ArgumentParser(
        prog="Wall_e Runner",
        description="automates the process for running wall_e"
    )

    parser_obj.add_argument(
        "--env_file", action='store_true', default=False,
        help=f"Indicator of whether to pull the environment variables from the file '{ENV_FILE_LOCATION}'. Helpful if "
             f"the script has already been run and created the CI/user_scripts/wall_e.env file."
    )
    parser_obj.add_argument(
        "--overwrite_env_file", action='store_true',
        help="indicator to the script that while you are pulling the env variables using --env_file, you want to "
             "overwrite some of the imported variables"
    )
    parser_obj.add_argument(
        '--dockerized_wall_e', action='store', default=None, choices=['true', 'false'],
        help="indicates whether or not to run wall_e in a docker container."
    )
    parser_obj.add_argument(
        '--database_type', action='store', default=None,
        choices=[DatabaseType.sqlite3.value, DatabaseType.postgreSQL.value],
        help="indicates whether you want to use sqlite3 or postgres for the database type."
    )
    parser_obj.add_argument(
        "--wall_e_models_location", action='store', default=None,
        help="used to specify the absolute path to the wall_e_models", metavar="/path/to/wall_e_model/repo"
    )
    parser_obj.add_argument(
        "--launch_wall_e", action='store', default=None, choices=['true', 'false'], help="script will run wall_e."
    )
    parser_obj.add_argument(
        "--install_requirements", action='store', default=None, choices=['true', 'false'],
        help="script will install the required python modules."
    )
    parser_obj.add_argument(
        "--setup_database", action='store', default=None, choices=['true', 'false'],
        help="script will setup a fresh database."
    )
    return parser_obj


def convert_command_line_argument_to_menu_format(arg):
    """
    Converts the command-line boolean value into the same format as the menu takes in from the user
    :param arg:
    :return:
    """
    if arg == 'true':
        return 'y'
    elif arg == 'false':
        return 'n'
    return None


def pull_variable_from_command_line_arguments(argparser):
    """

    :param argparser: the argparse object
    :return: (
        the dockerized_wall_e command-line flag
        the database type command-line flag
        the wall_e_models location
        the launch_wall_e command-line flag
        the install_requirements command-line flag
        the setup_database command-line flag
    )
    """
    database_type = None
    if argparser.database_type == DatabaseType.sqlite3.value:
        database_type = DatabaseType.sqlite3.value
    elif argparser.database_type == DatabaseType.postgreSQL.value:
        database_type = DatabaseType.postgreSQL.value
    return (
        convert_command_line_argument_to_menu_format(argparser.dockerized_wall_e), database_type,
        argparser.wall_e_models_location, convert_command_line_argument_to_menu_format(argparser.launch_wall_e),
        convert_command_line_argument_to_menu_format(argparser.install_requirements),
        convert_command_line_argument_to_menu_format(argparser.setup_database)

    )


def import_env_variables_from_env_file():
    """

    :return: overwrite_env_file -- the overwrite_env_file command-line flag indicating if the user wants to
     overwrite any env variables from the env file
    """
    overwrite_env_file = False
    if os.path.exists(ENV_FILE_LOCATION) if args.env_file else False:
        subprocess.getstatusoutput("python3 -m pip install python-dotenv")
        from dotenv import load_dotenv

        dotenv_path = Path(ENV_FILE_LOCATION)
        load_dotenv(dotenv_path=dotenv_path)
        if os.path.exists(RUN_ENV_FILE_LOCATION):
            load_dotenv(dotenv_path=RUN_ENV_FILE_LOCATION)
        overwrite_env_file = args.overwrite_env_file
    return overwrite_env_file


def check_for_null_variables(**kwargs):
    """
    Indicator of whether any of the variables in the dict are None
    :param kwargs: a dictionary of the necessary keys
    :return: True, key if any of the necessary Keys are None and False, None otherwise
    """
    for key, value in kwargs.items():
        if value is None:
            return True, key
    return False, None


def get_boolean_variable(message, variable_name, description=None, command_line_argument=None, overwrite_env=False,
                         default_is_yes=True):
    """

    :param message: the message for the variable when taking in the user's input
    :param variable_name: the key for the variable in the environment
    :param description: the description for the message when taking in the user's input
    :param command_line_argument: the command-line argument that the user may have set
    :param overwrite_env: indicator of whether the user has requested to overwrite the env variable that was detected
     in the .env file
    :param default_is_yes: indicates if the default boolean is a Yes or No if the user chooses to skip
    :return: Boolean
    """
    if command_line_argument is not None:
        # user specified the variable in the command-line so no need to ask the user anything
        if command_line_argument.lower() == 'y':
            return True
        elif command_line_argument.lower() == 'n':
            return False
    variable = os.environ.get(variable_name, None)
    if variable is None:
        # if the variable could not be detected on the command-line or via the environment
        # [which means it wasn't in the env files] then the user has to be asked
        default_value = 'y' if default_is_yes else 'n'
        variable = take_user_input_for_boolean_variable(
            variable_name, message, description=description, default_value=default_value,
            default_is_yes=default_is_yes, is_default_value=True
        )
    else:
        variable = 'y' if variable.lower() == 'true' else 'n'  # necessary since the environment variable that
        # is pulled from the env file is either 'True' or 'False'
        if overwrite_env:
            # if the variable was in the environment but the user requested to the option of overriding it
            variable = take_user_input_for_boolean_variable(
                variable_name, message, description=description, default_value=variable, default_is_yes=default_is_yes,
                is_default_value=variable == default_value
            )
    return variable == 'y'


def take_user_input_for_boolean_variable(variable_name, message, description=None, default_value=None,
                                         default_is_yes=True, is_default_value=False):
    """

    :param variable_name: the key for the variable in the environment
    :param message: the message for the variable when taking in the user's input
    :param description: the description for the message when taking in the user's input
    :param default_value: the default value to use if the user chooses to skip answering the variable
    :param default_is_yes: indicates if the default boolean is a Yes or No if the user chooses to skip
    :return: y/n string
    """
    message = f"\n{message}"
    message += "\nOptions for answer: " + ("Y/n" if default_is_yes else "y/N")
    choices = ['y', 'n']
    if choices is None:
        raise Exception(f"no choices detected for variable {variable_name}")
    if default_value is not None:
        choices.append("s")
        message += (
            f"\n[or press s to skip and revert to the {'default' if is_default_value else ''}"
            f"value of '{default_value}']"
        )
    if description is not None:
        message += f"\n{description}"
    message += "\n"
    user_input = input(message).lower()
    while user_input not in choices:
        user_input = input("Please try again\n").lower()
    if user_input == 's':
        user_input = default_value
    return user_input


def get_string_variables(message, variable_name, description=None, command_line_argument=None, overwrite_env=False,
                         default_value=None, choices=None):
    """

    :param message: the message for the variable when taking in the user's input
    :param variable_name: the key for the variable in the environment
    :param description: the description for the message when taking in the user's input
    :param command_line_argument: the command-line argument that the user may have set
    :param overwrite_env: indicator of whether the user has requested to overwrite the env variable that was detected
     in the .env file
    :param default_value: the default string value to use of the variable
    :param choices: the choices that a user can select from for a variable, if it's not an open-ended string variable
    :return: the string for the environment variable
    """
    if command_line_argument is not None:
        # user specified the variable in the command-line so no need to ask the user anything
        return command_line_argument
    variable = os.environ.get(variable_name, None)
    if variable is None:
        variable = take_user_input_for_string_variable(
            message, description=description, default_value=default_value, choices=choices, is_default_value=True
        )
    elif overwrite_env:
        variable = take_user_input_for_string_variable(
            message, description=description, default_value=variable, choices=choices, is_default_value=variable == default_value
        )
    return variable


def take_user_input_for_string_variable(message, description=None, default_value=None, choices=None,
                                        is_default_value=False):
    """

    :param message: the message for the variable when taking in the user's input
    :param description: the description for the message when taking in the user's input
    :param default_value: the default string value to use of the variable
    :param choices: the choices that a user can select from for a variable, if it's not an open-ended string variable
    :return: the string for the environment variable
    """
    message = f"\n{message}"
    if choices is not None:
        message += "\nOptions for answer: " + ", ".join(choices)
    if default_value is not None:
        if choices is not None:
            choices.append("s")
        message += (
            f"\n[or press s to skip and revert to the {'default' if is_default_value else ''}"
            f"value of '{default_value}']"
        )
    if description is not None:
        message += f"\n{description}"
    message += "\n"
    user_input = input(message).strip()
    if choices is not None:
        lower_case_choices = [choice.lower() for choice in choices]
        while user_input.lower() not in lower_case_choices:
            user_input = input("Please try again\n").strip()
    else:
        while (user_input.lower() == 's' or user_input == '') and default_value is None:
            # doing the only error checking that
            # can be done with an open-ended string variable where no default value is specified
            user_input = input("Please try again\n").strip()
    if user_input.lower() == "s":
        user_input = default_value
    return user_input


parser = create_argument_parser()
args = parser.parse_args()

(
    basic_config__DOCKERIZED_CMD_LINE_ARGUMENT, database_config__TYPE_CMD_LINE_ARGUMENT,
    WALL_E_MODEL_PATH_CMD_LINE_ARGUMENT, LAUNCH_WALL_E_CMD_LINE_ARGUMENT, INSTALL_REQUIREMENTS_CMD_LINE_ARGUMENT,
    SETUP_DATABASE_CMD_LINE_ARGUMENT
) = pull_variable_from_command_line_arguments(args)

overwrite_env_file = import_env_variables_from_env_file()


basic_config__TOKEN = get_string_variables(
    "What is your discord bot's token?",
    "basic_config__TOKEN",
    description="Instructions to get Token: https://discord.com/developers/docs/getting-started",
    overwrite_env=overwrite_env_file
)
basic_config__GUILD_ID = get_string_variables(
    "What is your discord guild's ID?",
    "basic_config__GUILD_ID",
    description=(
        "Instructions to get guild ID: "
        "\n - https://discord.com/developers/docs/game-sdk/store"
        "\n - https://github.com/CSSS/wall_e/blob/master/documentation/Working_on_Bot/pictures/get_guild_id.png"
    ),
    overwrite_env=overwrite_env_file
)
basic_config__DOCKERIZED = get_boolean_variable(
    "Do you want to use a dockerized wall_e?", "basic_config__DOCKERIZED",
    description=(
        "A dockerized wall_e is harder to debug but you might run into OS compatibility issues with some of "
        "the python modules"
    ),
    command_line_argument=basic_config__DOCKERIZED_CMD_LINE_ARGUMENT,
    overwrite_env=overwrite_env_file, default_is_yes=False
)

if basic_config__DOCKERIZED is False:
    database_config__TYPE = get_string_variables(
        "What database do you want to use?", "database_config__TYPE",
        command_line_argument=database_config__TYPE_CMD_LINE_ARGUMENT,
        overwrite_env=overwrite_env_file, default_value=DatabaseType.sqlite3.value,
        choices=[DatabaseType.sqlite3.value, DatabaseType.postgreSQL.value]
    )
else:
    database_config__TYPE = DatabaseType.postgreSQL.value
basic_config__DOCKERIZED = 1 if basic_config__DOCKERIZED else 0
if (database_config__TYPE == DatabaseType.postgreSQL.value) and (platform.system() != "Linux"):
    print("Sorry, looks like you are using a non-Linux system and are trying to use the dockerized database, "
          "which this script does not currently support :-(")
    print("Feel free to add that feature in or revert to using db.sqlite3")
    exit(1)

WALL_E_MODEL_PATH = WALL_E_MODEL_PATH_CMD_LINE_ARGUMENT
while WALL_E_MODEL_PATH is None or not os.path.exists(WALL_E_MODEL_PATH):
    WALL_E_MODEL_PATH = get_string_variables(
        "Please specify the relative/absolute path for the wall_e_model in the form /path/to/wall_e_model/repo",
        "WALL_E_MODEL_PATH",
        command_line_argument=WALL_E_MODEL_PATH, overwrite_env=overwrite_env_file,
        default_value=WALL_E_MODEL_PATH
    )
    if WALL_E_MODEL_PATH is not None and not os.path.exists(WALL_E_MODEL_PATH):
        print(f"path {WALL_E_MODEL_PATH} does not exist")
LAUNCH_WALL_E = get_boolean_variable(
    "Do you you want this script to launch wall_e? [the alternative is to use PyCharm]", "LAUNCH_WALL_E",
    command_line_argument=LAUNCH_WALL_E_CMD_LINE_ARGUMENT, overwrite_env=overwrite_env_file
)
INSTALL_REQUIREMENTS = get_boolean_variable(
    "Do you you want this script to install the python requirements?", "INSTALL_REQUIREMENTS",
    command_line_argument=INSTALL_REQUIREMENTS_CMD_LINE_ARGUMENT, overwrite_env=overwrite_env_file,
    default_is_yes=False
)
SETUP_DATABASE = get_boolean_variable(
    "Do you you want this script to setup the database?", "SETUP_DATABASE",
    command_line_argument=SETUP_DATABASE_CMD_LINE_ARGUMENT, overwrite_env=overwrite_env_file
)
channel_names__BOT_GENERAL_CHANNEL = get_string_variables(
    "What name do you want to set for the channel that the bot takes in the RoleCommands on? ",
    "channel_names__BOT_GENERAL_CHANNEL", overwrite_env=overwrite_env_file,
    default_value='bot-commands-and-misc'
)
channel_names__MOD_CHANNEL = get_string_variables(
    "What name do you want to set for the channel that bot sends ban related messages on? ",
    "channel_names__MOD_CHANNEL", overwrite_env=overwrite_env_file,
    default_value='council-summary'
)
channel_names__LEVELLING_CHANNEL = get_string_variables(
    "What name do you want to set for the channel that bot sends XP level related messages on? ",
    "channel_names__LEVELLING_CHANNEL", overwrite_env=overwrite_env_file,
    default_value='council'
)
channel_names__ANNOUNCEMENTS_CHANNEL = get_string_variables(
    "What name do you want to set for the channel that announcements are sent on? ",
    "channel_names__ANNOUNCEMENTS_CHANNEL", overwrite_env=overwrite_env_file,
    default_value='announcements'
)
channel_names__EMBED_AVATAR_CHANNEL = get_string_variables(
    "What name do you want to set for the channel where embed avatars are stored? ",
    "channel_names__EMBED_AVATAR_CHANNEL", overwrite_env=overwrite_env_file,
    default_value='embed_avatars'
)
channel_names__INCIDENT_REPORT_CHANNEL = get_string_variables(
    "What name do you want to set for the channel where incident reports are sent? ",
    "channel_names__INCIDENT_REPORT_CHANNEL", overwrite_env=overwrite_env_file,
    default_value='incident_reports'
)
channel_names__LEVELLING_WEBSITE_AVATAR_IMAGE_CHANNEL = get_string_variables(
    "What name do you want to set for the channel where the images used on the levelling website are sent? ",
    "channel_names__LEVELLING_WEBSITE_AVATAR_IMAGE_CHANNEL", overwrite_env=overwrite_env_file,
    default_value='leveling_website_avatar_images'
)
channel_names__BOT_MANAGEMENT_CHANNEL = get_string_variables(
    "What name do you want to set for the channel where errors from the ban interceptions embed creations are sent? ",
    "channel_names__BOT_MANAGEMENT_CHANNEL", overwrite_env=overwrite_env_file,
    default_value='bot_management'
)


essential_variables_are_null = check_for_null_variables(
    basic_config__TOKEN=basic_config__TOKEN, basic_config__GUILD_ID=basic_config__GUILD_ID,
    basic_config__DOCKERIZED=basic_config__DOCKERIZED, WALL_E_MODEL_PATH=WALL_E_MODEL_PATH
)
if essential_variables_are_null[0]:
    raise Exception(f"necessary variable {essential_variables_are_null[1]} is None")

basic_config__COMPOSE_PROJECT_NAME = 'discord_bot'
database_config__HOST = None
database_config__DB_PORT = 5433

if basic_config__DOCKERIZED == 1:
    database_config__TYPE = DatabaseType.postgreSQL.value
    database_config__HOST = f"{basic_config__COMPOSE_PROJECT_NAME}_wall_e_db"
elif database_config__TYPE == DatabaseType.postgreSQL.value:
    database_config__HOST = "127.0.0.1"
    database_config__DB_PORT = 5433


database_config = ""
if database_config__TYPE == "postgreSQL":
    if basic_config__DOCKERIZED != 1:
        database_config += f"""database_config__DB_PORT='{database_config__DB_PORT}'
database_config__HOST='{database_config__HOST}'
"""
    database_config += f"""database_config__WALL_E_DB_DBNAME='csss_discord_db'
database_config__WALL_E_DB_USER='wall_e'
database_config__WALL_E_DB_PASSWORD='wallEPassword'"""


with open(ENV_FILE_LOCATION, "w") as f:
    f.seek(0)
    f.write(f"""basic_config__TOKEN='{basic_config__TOKEN}'
basic_config__ENVIRONMENT='LOCALHOST'
basic_config__COMPOSE_PROJECT_NAME='{basic_config__COMPOSE_PROJECT_NAME}'
basic_config__GUILD_ID='{basic_config__GUILD_ID}'
basic_config__DOCKERIZED='{basic_config__DOCKERIZED}'

channel_names__BOT_GENERAL_CHANNEL='{channel_names__BOT_GENERAL_CHANNEL}'
channel_names__MOD_CHANNEL='{channel_names__MOD_CHANNEL}'
channel_names__LEVELLING_CHANNEL='{channel_names__LEVELLING_CHANNEL}'
channel_names__EMBED_AVATAR_CHANNEL='{channel_names__EMBED_AVATAR_CHANNEL}'
channel_names__INCIDENT_REPORT_CHANNEL='{channel_names__INCIDENT_REPORT_CHANNEL}'
channel_names__LEVELLING_WEBSITE_AVATAR_IMAGE_CHANNEL='{channel_names__LEVELLING_WEBSITE_AVATAR_IMAGE_CHANNEL}'
channel_names__ANNOUNCEMENTS_CHANNEL='{channel_names__ANNOUNCEMENTS_CHANNEL}'
channel_names__BOT_MANAGEMENT_CHANNEL='{channel_names__BOT_MANAGEMENT_CHANNEL}'

database_config__TYPE='{database_config__TYPE}'
{database_config}""")

with open(RUN_ENV_FILE_LOCATION, "w") as f:
    f.seek(0)
    f.write(f"""LAUNCH_WALL_E='{LAUNCH_WALL_E}'
WALL_E_MODEL_PATH='{WALL_E_MODEL_PATH}'
POSTGRES_PASSWORD='postgres_passwd'
ORIGIN_IMAGE='sfucsssorg/wall_e'
HELP_SELECTED='0'
INSTALL_REQUIREMENTS='{INSTALL_REQUIREMENTS}'
SETUP_DATABASE='{SETUP_DATABASE}'""")
