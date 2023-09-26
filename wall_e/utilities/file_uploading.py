from utilities.log_channel import write_to_bot_log_channel


async def start_file_uploading(logger, guild, bot, config, file_path, channel_name):
    """
    Handles getting the necessary ID of the channel that is then used to upload the log file entries to
    :param logger: the logger instance of the calling service
    :param guild: the guild that wall_e is running in
    :param bot: necessary for getting the channel id and creating the task of uploading to the discord channel
    :param config: used to determine the name of the text channels if the environment is TEST and used to
     determine the gmail credentials
    :param file_path: the path of the file to upload to the text channel
    :param channel_name: the name to set for the file log channel
    :return:
    """
    logger.info(f"[file_uploading.py start_file_uploading()] trying to open {file_path} to be able to send "
                f"its output to #{channel_name} channel")
    chan_id = await bot.bot_channel_manager.create_or_get_channel_id_for_service(
        logger, guild, config, channel_name
    )
    bot.loop.create_task(
        write_to_bot_log_channel(
            logger, config, bot, file_path, chan_id, 'error' in channel_name
        )
    )
    logger.info(
        f"[file_uploading.py start_file_uploading()] {file_path} successfully opened and connection to "
        f"{channel_name} channel has been made"
    )
