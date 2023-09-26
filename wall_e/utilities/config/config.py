
import os
import configparser


config_file_location_local = "utilities/config/local.ini"
config_file_location_dev = "utilities/config/dev.ini"
config_file_location_production = "utilities/config/production.ini"

cog_location_python_path = "cogs."


class WallEConfig:
    def __init__(self, environment, wall_e=True):
        # wall_e flag is needed to ensure that the environment variables aren't wiped clean until after
        # they have been used by the django-orm for the database migrations and connection

        self.config = configparser.ConfigParser(interpolation=None)
        self.config.optionxform = str
        if environment == "LOCALHOST":
            self.config.read(config_file_location_local)
        elif environment == 'TEST':
            self.config.read(config_file_location_dev)
        elif environment == "PRODUCTION":
            self.config.read(config_file_location_production)
        else:
            raise Exception(f"[WallEConfig __init__()] incorrect environment specified {environment}")

        for each_section in self.config.sections():
            for (key, value) in self.config.items(each_section):
                environment_var = f"{each_section}__{key}"
                if environment_var in os.environ:
                    self.set_config_value(each_section, key, os.environ[environment_var])
                    if wall_e:
                        os.environ[environment_var] = ' '

    def get_config_value(self, section, option):

        if self.config.has_option(section, option) and self.config.get(section, option) != '':
            return self.config.get(section, option)

        print(
            f"[WallEConfig get_config_value()] no key found for option {option} under section {section}"
        )
        return None

    def enabled(self, section, option="ENABLED"):

        return self.config.get(section, option) == "1"

    def set_config_value(self, section, option, value):
        if self.config.has_option(section, option):
            print(
                f"[WallEConfig set_config_value()] setting value for section "
                f"[{section}] option [{option}]"
            )
            self.config.set(section, option, fr'{value}')
        else:
            raise KeyError(f"Section '{section}' or Option '{option}' does not exist")

    def get_cogs(self):

        def cog_can_be_loaded(cog):
            return (
                (cog != 'reminders') or
                (cog == 'reminders' and self.enabled("database_config", option="ENABLED"))
            )

        cogs = [
            {'name': cog, 'path': cog_location_python_path}
            for cog in self.config['cogs']
            if self.enabled("cogs", cog) == 1 and cog_can_be_loaded(cog)
        ]
        return cogs
