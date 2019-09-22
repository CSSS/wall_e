
import os
import json
import configparser

config_file_location_local = "resources/utilities/config/local.ini"
config_file_location_prouction = "resources/utilities/config/production.ini"
config_file_location_dev = "resources/utilities/config/dev.ini"

cog_location_python_path = "resources.cogs."

help_json_location = "resources/locales/"
help_json_file_name = "help.json"


class WalleConfig():
    def __init__(self, environment):
        config = configparser.ConfigParser()
        config.optionxform = str
        if (environment == "LOCALHOST"):
            config.read(config_file_location_local)
        elif (environment == 'DEV'):
            config.read(config_file_location_dev)
        elif (environment == "PRODUCTION"):
            config.read(config_file_location_prouction)
        else:
            print("incorrect environment specified {}".format(environment))
        self.config = {}
        self.config['wall_e'] = config

    def get_config_value(self, section, option):
        if option in os.environ:
            return os.environ[option]

        if self.config['wall_e'].has_option(section, option):
            return self.config['wall_e'].get(section, option)

        return 'NONE'

    def enabled(self, section, option="enabled"):
        if option in os.environ:
            return os.environ[option] == "1"

        return self.config["wall_e"].get(section, option) == "1"

    def set_config_value(self, section, option, value):
        if self.config['wall_e'].has_option(section, option):
            self.config['wall_e'].set(section, option, str(value))
        else:
            raise KeyError("Section '{}' or Option '{}' does not exist".format(section, option))

    def cog_enabled(self, name_of_cog):
        return (self.config['cogs_enabled'][name_of_cog] == 1)

    def get_cogs(self):
        cogs_to_load = []
        cogs = self.config['wall_e']
        for cog in cogs['cogs_enabled']:
            if int(cogs['cogs_enabled'][cog]) == 1:
                cogDict = {}
                cogDict['name'] = cog
                cogDict['path'] = cog_location_python_path
                cogs_to_load.append(cogDict)
        return cogs_to_load

    def get_help_json(self):
        with open(help_json_location + help_json_file_name) as f:
            helpDict = json.load(f)
        return helpDict
