from utilities.error_reporter import error_reporter
from utilities.log_channel import write_to_bot_log_channel


async def start_file_uploading(logger, guild, bot, config, file_path, channel_name, categorized_channel=True):
    """
    Handles getting the necessary ID of the channel that is then used to upload the log file entries to
    :param logger: the logger instance of the calling service
    :param guild: the guild that wall_e is running in
    :param bot: necessary for getting the channel id and creating the task of uploading to the discord channel
    :param config: used to determine the gmail credentials
    :param file_path: the path of the file to upload to the text channel
    :param channel_name: the name to set for the file log channel
    :param categorized_channel: flag to indicate whether the channel that will be created is under the Logs category
    :return:
    """
    logger.debug(f"[file_uploading.py start_file_uploading()] trying to open {file_path} to be able to send "
                 f"its output to #{channel_name} channel")
    if categorized_channel:
        chan_id = await bot.bot_channel_manager.create_or_get_channel_id_for_service(
            logger, guild, config, channel_name
        )
    else:
        chan_id = await bot.bot_channel_manager.create_or_get_channel_id(
            logger, guild, config.get_config_value('basic_config', 'ENVIRONMENT'), channel_name
        )
    bot.loop.create_task(
        write_to_bot_log_channel(
            logger, config, bot, file_path, chan_id
        )
    )
    bot.loop.create_task(
        error_reporter(config, file_path)
    )
    logger.debug(
        f"[file_uploading.py start_file_uploading()] {file_path} successfully opened and connection to "
        f"{channel_name} channel has been made"
    )
