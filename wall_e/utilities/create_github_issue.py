import re

import requests


def create_github_issue(error_messages, config):
    """
    Files a wall_e error as an issue under the repo

    :param error_messages: the error stack trace to include in the body of the github issue
    :param config: used to determine the github csss-admin credentials
    :return:
    """
    open_issues = requests.get(
        url="https://api.github.com/repos/csss/wall_e/issues?state=open&creator=csss-admin",
        headers={
            "Accept": "application/vnd.github+json"
        }
    ).json()
    if len(open_issues) > 0:
        # exiting the function so that multiple identical issues don't get created by the bot everytime.
        # this once led to 1500 issues being created on the wall_e repo for the exact same problem
        return
    last_message = None
    error_message_body = "".join(error_messages)
    if "/usr/src/app/" in error_message_body:  # if the directory that contains the WALL_E code is in the stacktrace
        # then it is probably a guarantee that the issue is due to WALL_E and not a problem with discord.py
        # or a network glitch
        last_line = len(error_messages) - 1
        while last_line > -1:
            if error_messages[last_line] != "\n":
                last_message = error_messages[last_line]
                last_line = -1
            else:
                last_line -= 1
        beginning_of_error_message = re.match(
            r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} = ERROR = ", last_message
        )
        beginning_of_error_message = beginning_of_error_message.regs[0][1] if beginning_of_error_message else 0
        last_message = last_message[beginning_of_error_message:]
        discord_internet_issues = [
            "503 Service Unavailable (error code: 0): upstream connect error or disconnect/reset before headers. "
            "reset reason: remote connection failure, transport failure reason: immediate connect error: No such "
            "file or directory",
            "503 Service Unavailable (error code: 0): upstream connect error or disconnect/reset before headers. "
            "reset reason: connection termination",
            "discord.errors.ConnectionClosed: Shard ID None WebSocket closed with 1000"
        ]
        if last_message not in discord_internet_issues:
            requests.post(
                url="https://api.github.com/repos/csss/wall_e/issues",
                headers={
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {config.get_config_value('github', 'TOKEN')}"
                },
                json={
                    "title": last_message,
                    "body": f"```\n{error_message_body}\n```"
                }
            )
