#!/bin/bash

set -e

echo -e "\n[y/N] indicates a yes/no question. the default is the letter in CAPS. If answer is not understood, will revert to default\n"

if [ "${1}" == "--env_file" ];
then
	export run_through_setup="y";
	read_from_env_file="true";
	cd wall_e
	. ../CI/user_scripts/set_env.sh
	cd -
	if [[ "${basic_config__DOCKERIZED}" == "y" ]];
	then
		export basic_config__DOCKERIZED='1'
	else
		export basic_config__DOCKERIZED='0'
	fi
	if [[ "${database_config__TYPE}" == "postgresSQL" ]];
	then
		export postgres_database='y'
		export sqlite3_database='n'
	else
		export postgres_database='n'
		export sqlite3_database='y'
	fi
else
	echo "Do you need to run through the setup? [y/N]"
	read run_through_setup
fi

if [ "${run_through_setup}" == "y" ];
then
	if [ -z "${basic_config__TOKEN}" ];
	then
		echo "What is your discord bot's token? [see https://discord.com/developers/docs/getting-started if you are not sure how to get it]"
		read basic_config__TOKEN
	fi

	if [ -z "${basic_config__GUILD_ID}" ];
	then
		echo "What is your discord guild's ID? [see https://discord.com/developers/docs/game-sdk/store and https://github.com/CSSS/wall_e/blob/master/documentation/Working_on_Bot/pictures/get_guild_id.png to see where to get it]"
		read basic_config__GUILD_ID
	fi

	use_defaults="false";

	if [ "${1}" == "--default" ];
	then
		use_defaults="true";
		sqlite3_database="y";
		launch_wall_e="y";
		postgres_database="n";
	fi

	if [ -z "${basic_config__DOCKERIZED}" ];
	then
		echo "Do you want to use a dockerized wall_e? [y/N] a dockerized wall_e is harder to debug but you might run into OS compatibility issues with some of the python modules"
		read basic_config__DOCKERIZED
		if [[ "${basic_config__DOCKERIZED}" == "y" ]];
		then
			export basic_config__DOCKERIZED='1'
		else
			export basic_config__DOCKERIZED='0'
		fi
	fi

	if [[ "$OSTYPE" == "linux-gnu"* ]];
	then
		supported_os="true"
	else
		supported_os="false"
	fi

	if [[ "${use_defaults}" != "true" && -z "${channel_names__BOT_GENERAL_CHANNEL}" ]];
	then
		echo "What name do you want to set for the channel that the bot takes in the RoleCommands on? [enter nothing to revert to default]"
		read channel_names__BOT_GENERAL_CHANNEL
	fi
	if [ -z "${channel_names__BOT_GENERAL_CHANNEL}" ];
	then
		channel_names__BOT_GENERAL_CHANNEL="bot-commands-and-misc"
	fi


	if [[ "${use_defaults}" != "true" && -z "${channel_names__MOD_CHANNEL}" ]];
	then
		echo "What name do you want to set for the channel that bot sends ban related messages on? [enter nothing to revert to default]"
		read channel_names__MOD_CHANNEL
	fi
	if [ -z "${channel_names__MOD_CHANNEL}" ];
	then
		channel_names__MOD_CHANNEL="council-summary"
	fi


	if [[ "${use_defaults}" != "true" && -z "${channel_names__LEVELLING_CHANNEL}" ]];
	then
		echo "What name do you want to set for the channel that bot sends XP level related messages on? [enter nothing to revert to default]"
		read channel_names__LEVELLING_CHANNEL
	fi
	if [ -z "${channel_names__LEVELLING_CHANNEL}" ];
	then
		channel_names__LEVELLING_CHANNEL="council"
	fi

	if [[ "${use_defaults}" != "true" && -z "${channel_names__ANNOUNCEMENTS_CHANNEL}" ]];
	then
		echo "What name do you want to set for the channel that announcements are sent on? [enter nothing to revert to default]"
		read channel_names__ANNOUNCEMENTS_CHANNEL
	fi
	if [ -z "${channel_names__ANNOUNCEMENTS_CHANNEL}" ];
	then
		channel_names__ANNOUNCEMENTS_CHANNEL="announcements"
	fi

	if [ "${use_defaults}" != "true" ];
	then
		echo "Do you you want this script to launch wall_e? [Yn] [the alternative is to use PyCharm]"
		read launch_wall_e
	fi

	echo 'basic_config__TOKEN='"'"${basic_config__TOKEN}"'" > CI/user_scripts/wall_e.env
	echo 'basic_config__ENVIRONMENT='"'"'LOCALHOST'"'" >> CI/user_scripts/wall_e.env
	echo 'basic_config__COMPOSE_PROJECT_NAME='"'"'discord_bot'"'" >> CI/user_scripts/wall_e.env
	echo 'basic_config__GUILD_ID='"'"${basic_config__GUILD_ID}"'" >> CI/user_scripts/wall_e.env
	if [[ "${basic_config__DOCKERIZED}" == "y" ]];
	then
		if [[ "${supported_os}" == "false" ]];
		then
			echo "sorry, script is not currently setup to use anything other than a dockerized posgtres database on non-linux system :-("
			echo "Please feel free to add that feature in"
		exit 1
		fi
		echo -e 'basic_config__DOCKERIZED='"'1'\n\n" >> CI/user_scripts/wall_e.env
	else
		echo -e 'basic_config__DOCKERIZED='"'0'\n\n" >> CI/user_scripts/wall_e.env
	fi

	echo 'channel_names__BOT_GENERAL_CHANNEL='"'"${channel_names__BOT_GENERAL_CHANNEL}"'" >> CI/user_scripts/wall_e.env
	echo 'channel_names__MOD_CHANNEL='"'"${channel_names__MOD_CHANNEL}"'" >> CI/user_scripts/wall_e.env
	echo 'channel_names__LEVELLING_CHANNEL='"'"${channel_names__LEVELLING_CHANNEL}"'" >> CI/user_scripts/wall_e.env
	echo -e 'channel_names__ANNOUNCEMENTS_CHANNEL='"'"${channel_names__ANNOUNCEMENTS_CHANNEL}"'\n\n" >> CI/user_scripts/wall_e.env

	export POSTGRES_PASSWORD='postgres_passwd'
	echo 'database_config__WALL_E_DB_DBNAME='"'"'csss_discord_db'"'" >> CI/user_scripts/wall_e.env
	echo 'database_config__WALL_E_DB_USER='"'"'wall_e'"'" >> CI/user_scripts/wall_e.env
	echo 'database_config__WALL_E_DB_PASSWORD='"'"'wallEPassword'"'" >> CI/user_scripts/wall_e.env
	echo 'database_config__ENABLED='"'"'1'"'" >> CI/user_scripts/wall_e.env

	if [[ "${basic_config__DOCKERIZED}" == "y" ]];
	then
		export COMPOSE_PROJECT_NAME="discord_bot"

		echo 'database_config__TYPE='"'"'postgresSQL'"'" >> CI/user_scripts/wall_e.env
		echo -e 'database_config__HOST='"'"${COMPOSE_PROJECT_NAME}_wall_e_db"'\n\n" >> CI/user_scripts/wall_e.env
		echo 'ORIGIN_IMAGE='"'"'sfucsssorg/wall_e'"'" >>  CI/user_scripts/wall_e.env
		echo 'POSTGRES_PASSWORD='"'"${POSTGRES_PASSWORD}"'" >> CI/user_scripts/wall_e.env
		cd wall_e
		. ../CI/user_scripts/set_env.sh
		../CI/user_scripts/setup-dev-env.sh
		docker logs -f "${COMPOSE_PROJECT_NAME}_wall_e"
	else
		if [[ "${use_defaults}" != "true" && -z "${sqlite3_database}" ]];
		then
			echo "Do you want to use db.sqlite3 for the database? [alternative is a separate service, dockerized or not] [Y/n]"
			read sqlite3_database
		fi


		if [[ "${sqlite3_database}" != "y" && -z "${postgres_database}" ]];
		then
			echo "Do you intended to use dockerized postgres? [Y/n]"
			read postgres_database
		fi

		if [[ "${postgres_database}" == "y" && "${supported_os}" == "false" ]];
		then
			echo "sorry, script is not currently setup to use anything other than a dockerized posgtres database on non-linux system :-("
			echo "Please feel free to add that feature in"
		exit 1
		fi

		if [ "${sqlite3_database}" != "y" ];
		then
			echo 'database_config__TYPE='"'"'postgresSQL'"'" >> CI/user_scripts/wall_e.env
			echo 'database_config__HOST='"'"'127.0.0.1'"'" >> CI/user_scripts/wall_e.env
			echo 'database_config__DB_PORT='"'"'5432'"'" >> CI/user_scripts/wall_e.env
		else
			echo 'database_config__TYPE='"'"'sqlite3'"'" >> CI/user_scripts/wall_e.env
			echo 'database_config__HOST='"'"'discord_bot_wall_e_db'"'" >> CI/user_scripts/wall_e.env
		fi

		cd wall_e

		wget https://raw.githubusercontent.com/CSSS/wall_e_python_base/master/layer-1-requirements.txt
		wget https://raw.githubusercontent.com/CSSS/wall_e_python_base/master/layer-2-requirements.txt
		python3 -m pip install -r layer-1-requirements.txt
		python3 -m pip install -r layer-2-requirements.txt
		rm layer-1-requirements.txt layer-2-requirements.txt

		python3 -m pip install -r requirements.txt

		. ../CI/user_scripts/set_env.sh

		if [[ "${sqlite3_database}" == "y" ]];
		then
			rm ../db.sqlite3 || true
		else
			sudo apt-get install postgresql-contrib
			docker rm -f "${basic_config__COMPOSE_PROJECT_NAME}_wall_e_db"
			sleep 4
			docker run -d --env POSTGRES_PASSWORD=${POSTGRES_PASSWORD} -p \
			"${database_config__DB_PORT}":5432 --name "${basic_config__COMPOSE_PROJECT_NAME}_wall_e_db" \
			postgres:alpine
			sleep 4
			PGPASSWORD=$POSTGRES_PASSWORD psql --set=WALL_E_DB_USER="${database_config__WALL_E_DB_USER}" \
			--set=WALL_E_DB_PASSWORD="${database_config__WALL_E_DB_PASSWORD}"  \
			--set=WALL_E_DB_DBNAME="${database_config__WALL_E_DB_DBNAME}" \
			-h "${database_config__HOST}" -p "${database_config__DB_PORT}"  -U "postgres" \
			-f ../CI/create-database.ddl
		fi

		python3 django_manage.py migrate
		rm wall_e.json* || true
		wget https://dev.sfucsss.org/wall_e/fixtures/wall_e.json
		python3 django_manage.py loaddata wall_e.json
		rm wall_e.json* || true

		if [ "${launch_wall_e}" == "n" ];
		then
			echo -e "\n\nSeems you are going to use something else to launch the bot. If you are going to use PyCharm, I HIGHLY recommend using https://github.com/ashald/EnvFile"
		fi
	fi
else
	launch_wall_e="y"
fi

if [ "${launch_wall_e}" != "n" ];
then
	echo "Launching the wall_e."
	sleep 3
	python3 main.py
fi