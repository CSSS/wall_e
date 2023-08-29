import os

from resources.utilities.config.config import WallEConfig

environment = os.environ['basic_config__ENVIRONMENT']
wall_e_config = WallEConfig(environment, wall_e=False)
postgres_sql = wall_e_config.enabled("database_config", "postgresSQL")

if postgres_sql:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': wall_e_config.get_config_value("database_config", "WALL_E_DB_DBNAME"),
            'USER': wall_e_config.get_config_value("database_config", "WALL_E_DB_USER"),
            'PASSWORD': wall_e_config.get_config_value("database_config", "WALL_E_DB_PASSWORD")
        }
    }

    if wall_e_config.enabled("basic_config", "DOCKERIZED"):
        DATABASES['default']['HOST'] = (
            f'{wall_e_config.get_config_value("basic_config", "COMPOSE_PROJECT_NAME")}_wall_e_db'
        )
    else:
        DATABASES['default']['PORT'] = wall_e_config.get_config_value("database_config", "DB_PORT")
        DATABASES['default']['HOST'] = wall_e_config.get_config_value("database_config", "HOST")

else:
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }

INSTALLED_APPS = (
    'WalleModels',
)

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

TIME_ZONE = 'Canada/Pacific'

USE_TZ = True

# Write a random secret key here
SECRET_KEY = '4e&6aw+(5&cg^_!05r(&7_#dghg_pdgopq(yk)xa^bog7j)^*j'
