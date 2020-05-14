#!/bin/bash

bot_token="${1}"
bot_manager_id_csss_guild="<@&321832268282855436>"

content="**New PR to Reviews**\n PR: # : ${pr_url} \nRequired Reviewers: ${bot_manager_id_csss_guild} "

#my guild
bot_management_channel_id=466734608726229005

curl --header "Content-Type: application/json" \
 --request POST -H "Authorization: Bot ${bot_token}" \
   --data "{\"content\":\"${content}\"}" \
   https://discordapp.com/api/channels/${bot_management_channel_id}/messages
