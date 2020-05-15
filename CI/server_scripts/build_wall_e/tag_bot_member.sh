#!/bin/bash

set -e -o xtrace

bot_token="${1}"
pr_number="${2}"
pr_url="${3}"
channel_name_to_send_message_in="bot-management"
role_to_tag_in_message="bot_manager"

get_guild_id(){
  sleep 1
  val=$(curl --header "Content-Type: application/json" \
   --request GET -H "Authorization: Bot ${bot_token}" \
     https://discordapp.com/api/v6/users/@me/guilds)

  echo $val | jq -r '.[] | .id'
}

get_bot_manager_role_id(){
  sleep 1

  val=$(curl --header "Content-Type: application/json" \
  --request GET -H "Authorization: Bot ${bot_token}" \
    "https://discordapp.com/api/guilds/${guild_id}/roles")
  echo $val | jq -r ".[] | select(.name == \"${role_to_tag_in_message}\") | .id"
}

get_bot_management_channel_id(){
  sleep 1

  val=$(curl --header "Content-Type: application/json" \
  --request GET -H "Authorization: Bot ${bot_token}" \
    "https://discordapp.com/api/guilds/${guild_id}/channels")

  echo $val | jq -r ".[] | select(.name == \"${channel_name_to_send_message_in}\") | .id"
}

guild_id=$(get_guild_id)

bot_manager_role_id=$(get_bot_manager_role_id)

bot_management_channel_id=$(get_bot_management_channel_id)

content="**New PR to Review**\n PR# ${pr_number} \n${pr_url} \n<@&${bot_manager_role_id}>"

curl --header "Content-Type: application/json" \
 --request POST -H "Authorization: Bot ${bot_token}" \
   --data "{\"content\":\"${content}\"}" \
   https://discordapp.com/api/channels/${bot_management_channel_id}/messages
