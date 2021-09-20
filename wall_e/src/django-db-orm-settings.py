import os

from resources.utilities.config.config import WallEConfig

wall_e_config = WallEConfig(os.environ['ENVIRONMENT'])

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': wall_e_config.get_config_value("database_config", "WALL_E_DB_DBNAME"),
        'USER': wall_e_config.get_config_value("database_config", "WALL_E_DB_USER"),
        'PASSWORD': wall_e_config.get_config_value("database_config", "WALL_E_DB_PASSWORD"),
        'HOST': wall_e_config.get_config_value("database_config", "HOST"),
        'PORT': wall_e_config.get_config_value("database_config", "DB_PORT"),
    }
}

INSTALLED_APPS = (
    'WalleModels',
)

TIME_ZONE = 'Canada/Pacific'

USE_TZ = True

# Write a random secret key here
SECRET_KEY = '4e&6aw+(5&cg^_!05r(&7_#dghg_pdgopq(yk)xa^bog7j)^*j'
