#!/bin/bash

set -e -o xtrace
# https://stackoverflow.com/a/5750463/7734535

branch_name="${1}"
token="${2}"

deleted_discord_branch_channels () {
	branch_name="${1}"
	token="${2}"

	url="https://discordapp.com/api/users/@me/guilds"
	curl -H "Authorization: Bot ${token}"  "${url}" > output.json
	guild_id=$(cat output.json | jq -r .[].id)

	url="https://discordapp.com/api/guilds/${guild_id}/channels"
	curl -H "Authorization: Bot ${token}"  "${url}" > output.json
	mapfile -t list_of_channel_ids < <( cat output.json | jq -r .[].id )
	mapfile -t list_of_channel_names < <( cat output.json | jq -r .[].name )
	rm output.json

	for (( i=0; i<${#list_of_channel_ids[@]}; i++ ))
	do
		if [ "${list_of_channel_names[$i]}" = "${branch_name}" ]; then
			branch_id="${list_of_channel_ids[$i]}"
		fi

		if [ "${list_of_channel_names[$i]}" = "${branch_name}_logs" ]; then
			log_channel_id="${list_of_channel_ids[$i]}"
		fi

		if [ "${list_of_channel_names[$i]}" = "${branch_name}_reminders" ]; then
			reminder_channel_id="${list_of_channel_ids[$i]}"
		fi
	done
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

destroy_docker_resources () {
	export COMPOSE_PROJECT_NAME="TEST_${1}"
	./CI/destroy-dev-env.sh
	export wall_e_top_base_image=$(echo "${COMPOSE_PROJECT_NAME}_wall_e_base_image" | awk '{print tolower($0)}')
	export test_image_name=$(echo "${COMPOSE_PROJECT_NAME}_wall_e" | awk '{print tolower($0)}')
	export wall_e_bottom_base_image=$(echo "${COMPOSE_PROJECT_NAME}_wall_e_python_base_image" | awk '{print tolower($0)}')
	docker image rm "${wall_e_top_base_image}" || true
	docker image rm "${test_image_name}" || true
	docker image rm "${wall_e_bottom_base_image}" || true
	if [ ! -z "${JENKINS_HOME}" ]; then
			export commit_folder="wall_e_commits"
			export WALL_E_PYTHON_BASE_COMMIT_FILE="${JENKINS_HOME}/${commit_folder}/${COMPOSE_PROJECT_NAME}_python_base"
			export WALL_E_BASE_COMMIT_FILE="${JENKINS_HOME}/${commit_folder}/${COMPOSE_PROJECT_NAME}_wall_e_base"
			rm "${WALL_E_PYTHON_BASE_COMMIT_FILE}" || true
			rm "${WALL_E_BASE_COMMIT_FILE}" || true
	fi

}

deleted_discord_branch_channels "${branch_name}" "${token}"

destroy_docker_resources "${branch_name}"
