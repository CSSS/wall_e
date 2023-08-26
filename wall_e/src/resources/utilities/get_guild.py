def get_guild(bot, config):
    if config.get_config_value("basic_config", "ENVIRONMENT") != 'TEST':
        return bot.guild[0]
    guild_name = config.get_config_value("basic_config", "BRANCH_NAME")
    for guild in bot.guilds:
        if guild.name == guild_name:
            return guild
    return None
