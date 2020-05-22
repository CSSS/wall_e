#!/bin/bash

set -e -o xtrace
# https://stackoverflow.com/a/5750463/7734535

pr_number="${1}"
branch_name="${2}"
destination_branch_name="${3}"
merged="${4}"
action="${5}"
token="${6}"
WOLFRAM_API_TOKEN="${7}"

deleted_discord_pr_channels () {

	# Get Discord guild
	url="https://discordapp.com/api/users/@me/guilds"
	curl -H "Authorization: Bot ${token}"  "${url}" > output.json
	guild_id=$(cat output.json | jq -r .[].id)

	# Get guild\'s channels
	url="https://discordapp.com/api/guilds/${guild_id}/channels"
	curl -H "Authorization: Bot ${token}"  "${url}" > output.json
	mapfile -t list_of_channel_ids < <( cat output.json | jq -r .[].id )
	mapfile -t list_of_channel_names < <( cat output.json | jq -r .[].name )
	rm output.json


	for (( i=0; i<${#list_of_channel_ids[@]}; i++ ))
	do
		if [ "${list_of_channel_names[$i]}" = "pr-${pr_number}" ]; then
			branch_id="${list_of_channel_ids[$i]}"
		fi

		if [ "${list_of_channel_names[$i]}" = "pr-${pr_number}_logs" ]; then
			log_channel_id="${list_of_channel_ids[$i]}"
		fi

		if [ "${list_of_channel_names[$i]}" = "pr-${pr_number}_reminders" ]; then
			reminder_channel_id="${list_of_channel_ids[$i]}"
		fi
	done


	# Delete PR's channels (testing channel, log channel, reminders channel)
	if [ -z "${branch_id}" ]; then
		echo -e "\nbranch_id was not detected"
	else
		url="https://discordapp.com/api/channels/${branch_id}"
		curl -X DELETE -H "Authorization: Bot ${token}"  "${url}"
	fi

	if [ -z "${log_channel_id}" ]; then
		echo -e "\nlog_channel_id was not detected"
	else
		url="https://discordapp.com/api/channels/${log_channel_id}"
		curl -X DELETE -H "Authorization: Bot ${token}"  "${url}"
	fi

	if [ -z "${reminder_channel_id}" ]; then
		echo -e "\nreminder_channel_id was not detected"
	else
		url="https://discordapp.com/api/channels/${reminder_channel_id}"
		curl -X DELETE -H "Authorization: Bot ${token}"  "${url}"
	fi
}

if [ "${action}" = "closed" ]; then
	deleted_discord_pr_channels

	export COMPOSE_PROJECT_NAME="TEST_PR-${pr_number}"
	./CI/destroy-dev-env.sh

	# Restart a branch's containers if its PR to master was not merged
	if [[ "${merged}" = "false" && "${destination_branch_name}" = "master" ]]; then
		git checkout "${branch_name}"
		git pull origin "${branch_name}"
		export ENVIRONMENT=TEST;
		export BRANCH_NAME=${branch_name};
		export COMPOSE_PROJECT_NAME=TEST_${BRANCH_NAME};

		export POSTGRES_DB_USER=postgres;
		export POSTGRES_DB_DBNAME=postgres;
		export POSTGRES_PASSWORD=postgresPassword;

		export WALL_E_DB_USER=wall_e;
		export WALL_E_DB_DBNAME=csss_discord_db;
		export WALL_E_DB_PASSWORD=wallEPassword;
		export WOLFRAM_API_TOKEN=${WOLFRAM_API_TOKEN};
		export TOKEN=${token};
		export DISCORD_NOTIFICATION_MESSAGE_FILE=OUTPUT;

		./CI/server_scripts/build_wall_e/deploy-to-test-server.sh;
	fi
fi

# Stop a branch's containers if its PR to master is (re)opened
if [[ "${action}" = "opened" || "${action}" = "reopened" || "${action}" = "edited" ]] && [[ "${destination_branch_name}" = "master" ]]; then
	./CI/server_scripts/clean_branch/clear_branch_env.sh "${branch_name}" "${token}"
fi
