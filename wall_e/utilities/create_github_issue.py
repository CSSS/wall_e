import re

import requests


def create_github_issue(error_messages, config):
    last_message = error_messages[len(error_messages)-1]
    beginning_of_error_message = re.match(
        r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} = ERROR = \w* = ", last_message
    ).regs[0][1]
    last_message = last_message[beginning_of_error_message:]
    requests.post(
        url="https://api.github.com/repos/csss/wall_e/issues",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {config.get_config_value('github', 'TOKEN')}"
        },
        json={
            "title": last_message,
            "body": "```\n" + "\n".join(error_messages) + "\n```"
        }
    )
