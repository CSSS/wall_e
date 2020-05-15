#!/bin/bash

# set -e -o xtrace

bot_token="${1}"
pr_number="${2}"
pr_url="${3}"

Bot_manage_role_id=$(./CI/server_scripts/build_wall_e/get_bot_manager_ids.py -token "${bot_token}" -get_bot_manager_role_id)
sleep 1
bot_management_channel_id=$(./CI/server_scripts/build_wall_e/get_bot_manager_ids.py -token "${bot_token}" -get_bot_manager_channel_id)

echo "${Bot_manage_role_id}"
echo "${bot_management_channel_id}"

content="**New PR to Review**\n PR# ${pr_number} \n${pr_url} \n<@&${Bot_manage_role_id}>"


curl --header "Content-Type: application/json" \
 --request POST -H "Authorization: Bot ${bot_token}" \
   --data "{\"content\":\"${content}\"}" \
   https://discordapp.com/api/channels/${bot_management_channel_id}/messages
