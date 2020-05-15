#!/bin/bash


get_guild_roles(){
  /guilds/{guild.id}/roles

}
bot_token="${1}"
bot_manager_id_csss_guild="<@&321832268282855436>"
bot_manager_id_csss_guild="<@&710627204970840074>"
pr_number="${2}"
pr_url="${3}"

content="**New PR to Review**\n PR# ${pr_number} \n${pr_url} \n${bot_manager_id_csss_guild} "

#my guild
bot_management_channel_id=466734608726229005

curl --header "Content-Type: application/json" \
 --request POST -H "Authorization: Bot ${bot_token}" \
   --data "{\"content\":\"${content}\"}" \
   https://discordapp.com/api/channels/${bot_management_channel_id}/messages
