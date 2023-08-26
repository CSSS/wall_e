def get_guild(bot, config):
    env = config.get_config_value("basic_config", "ENVIRONMENT")
    if env != 'TEST':
        return bot.guilds[0]
    guild_name = config.get_config_value("basic_config", "BRANCH_NAME")
    for guild in bot.guilds:
        if guild.name == guild_name:
            return guild
    raise Exception(f"no guild found for {env}")
