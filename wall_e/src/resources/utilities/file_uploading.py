from resources.utilities.log_channel import write_to_bot_log_channel


async def start_file_uploading(bot, config, file_path, channel_name):
    print(f"trying to open {file_path} to be able to send "
          f"its output to #{channel_name} channel")
    chan_id = await bot.bot_loop_manager.create_or_get_channel_id_for_service(
        config, channel_name
    )
    bot.loop.create_task(
        write_to_bot_log_channel(
            bot, file_path, chan_id
        )
    )
    print(
        f"{file_path} successfully opened and connection to "
        f"{channel_name} channel has been made"
    )
