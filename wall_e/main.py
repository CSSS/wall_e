from utilities.global_vars import bot, wall_e_config

if __name__ == "__main__":
    bot.run(wall_e_config.get_config_value("basic_config", "TOKEN"))
