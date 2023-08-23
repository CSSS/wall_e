
import os
import json
import configparser
from collections import OrderedDict


config_file_dockerized_location_local = "resources/utilities/config/local.ini"
config_file_location_prouction = "resources/utilities/config/production.ini"
config_file_location_dev = "resources/utilities/config/dev.ini"

cog_location_python_path = "resources.cogs."

help_json_location = "resources/locales/"
help_json_file_name = "help.json"


class WallEConfig:
    def __init__(self, environment):
        config = configparser.ConfigParser(interpolation=None)
        config.optionxform = str
        if environment == "LOCALHOST":
            config.read(config_file_dockerized_location_local)
        elif environment == 'TEST':
            config.read(config_file_location_dev)
        elif environment == "PRODUCTION":
            config.read(config_file_location_prouction)
        else:
            raise Exception(f"[WallEConfig __init__()] incorrect environment specified {environment}")
        self.config = {'wall_e': config}

        # needed to ensure that the environment variables aren't wiped clean until after they have been used
        # by the django-orm for the database migrations and connection
        if 'DJANGO_SETTINGS_SET' not in os.environ:
            os.environ['DJANGO_SETTINGS_SET'] = "False"
        else:
            os.environ['DJANGO_SETTINGS_SET'] = "True"

        for each_section in self.config['wall_e'].sections():
            for (key, value) in self.config['wall_e'].items(each_section):
                if key in os.environ:
                    self.set_config_value(each_section, key, os.environ[key])
                    if os.environ['DJANGO_SETTINGS_SET'] == "True":
                        os.environ[key] = ' '

    def get_config_value(self, section, option):

        if self.config['wall_e'].has_option(section, option) and self.config['wall_e'].get(section, option) != '':
            return self.config['wall_e'].get(section, option)

        print(
            f"[WallEConfig get_config_value()] no key found for option {option} under section {section}"
        )
        return "NONE"

    def enabled(self, section, option="enabled"):

        return self.config["wall_e"].get(section, option) == "1"

    def set_config_value(self, section, option, value):
        if self.config['wall_e'].has_option(section, option):
            print(
                f"[WallEConfig set_config_value()] setting value for section "
                f"[{section}] option [{option}]"
            )
            self.config['wall_e'].set(section, option, fr'{value}')
        else:
            raise KeyError(f"Section '{section}' or Option '{option}' does not exist")

    def cog_enabled(self, name_of_cog):
        return self.config['cogs_enabled'][name_of_cog] == 1

    def get_cogs(self):
        cogs_to_load = []
        cogs = self.config['wall_e']
        for cog in cogs['cogs_enabled']:
            if int(cogs['cogs_enabled'][cog]) == 1 and ((cog != 'reminders') or
               (cog == 'reminders' and self.enabled("database_config", option="DB_ENABLED"))):
                cogs_to_load.append({'name': cog, 'path': cog_location_python_path})
        return cogs_to_load

    def get_help_json(self):
        with open(help_json_location + help_json_file_name) as f:
            help_dict = json.load(f, object_pairs_hook=OrderedDict)
        return help_dict
