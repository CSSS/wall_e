import asyncio
import re

from utilities.create_github_issue import create_github_issue


async def error_reporter(config, file_path):
    """
    Handles detecting any error stack traces in the sys debug log and reporting them both to github and emailing them
     to the bot-managers
    :param config: used to determine the gmail and github credentials
    :param file_path: the path of the file to scan for errors and upload to the text channel
    :return:
    """
    sys_debug_file = re.match(r"logs/sys/\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}_debug.log", file_path)
    if sys_debug_file:
        f = open(file_path, 'r')
        f.seek(0)
        error_lines = []
        error_pattern = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} = ERROR = ")
        non_error_pattern = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} = (INFO|DEBUG) = ")
        error_encountered = False
        log_issue = False
        while True:
            f.flush()
            lines = f.readlines()
            for line in lines:
                if error_pattern.match(line):
                    error_encountered = True
                    error_lines.append(line)
                elif non_error_pattern.match(line) and error_encountered:
                    log_issue = True
                elif error_encountered:
                    error_lines.append(line)
                elif non_error_pattern.match(line):
                    pass
                else:
                    pass
                if log_issue:
                    log_issue = False
                    error_encountered = False
                    create_github_issue(error_lines, config)
                    error_lines.clear()
            if len(lines) == 0 and error_encountered:
                log_issue = True
            if log_issue:
                log_issue = False
                error_encountered = False
                create_github_issue(error_lines, config)
                error_lines.clear()
            await asyncio.sleep(5)
