#!/bin/python3

import argparse
import requests

parser = argparse.ArgumentParser()
parser.add_argument("-token")
command_group = parser.add_mutually_exclusive_group(required=True)
command_group.add_argument("-get_bot_manager_role_id",action='store_true')
command_group.add_argument("-get_bot_manager_channel_id",action='store_true')

args = parser.parse_args()
bot_token = args.token

r = requests.get(
    "https://discordapp.com/api/v6/users/@me/guilds",
    headers={
    "Authorization" : "Bot {}".format(bot_token)
    }
)
guild_id=r.json()[0]['id']

def get_bot_manger_role_id():
    r = requests.get(
    "https://discordapp.com/api/guilds/{}/roles".format(guild_id),
    headers={
    "Authorization" : "Bot {}".format(bot_token)
    }
    )
    for val in r.json():
        if val['name'] == "bot_manager":
            return val['id']
    return "null"

def get_bot_manager_channel_id():
    r = requests.get(
        "https://discordapp.com/api/guilds/{}/channels".format(guild_id),
        headers={
            "Authorization" : "Bot {}".format(bot_token)
        }
    )
    for val in r.json():
        if val['name'] == "bot-management":
            return val['id']
    return "null"

if (args.get_bot_manager_role_id):
    print(get_bot_manger_role_id())
elif (args.get_bot_manager_channel_id):
    print(get_bot_manager_channel_id())
