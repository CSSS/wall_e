import logging
import psycopg2

logger = logging.getLogger('wall_e')


###############################
# SETUP DATABASE CONNECTION ##
###############################
def setupDB(config):
    if config.enabled("database"):
        try:
            env = config.get_config_value("wall_e", "ENVIRONMENT")
            compose_project_name = config.get_config_value("wall_e", "COMPOSE_PROJECT_NAME")
            postgres_db_dbname = config.get_config_value("database", "POSTGRES_DB_DBNAME")
            postgres_db_user = config.get_config_value("database", "POSTGRES_DB_USER")
            postgres_password = config.get_config_value("database", "POSTGRES_PASSWORD")
            wall_e_db_dbname = config.get_config_value("database", "WALL_E_DB_DBNAME")
            wall_e_db_user = config.get_config_value("database", "WALL_E_DB_USER")
            wall_e_db_password = config.get_config_value("database", "WALL_E_DB_PASSWORD")

            host = compose_project_name + '_wall_e_db'
            dbConnectionString = ("dbname='" + postgres_db_dbname + "' user='" + postgres_db_user + "' "
                                  "host='" + host + "' password='" + postgres_password + "'")
            logger.info("[main.py setupDB] Postgres User dbConnectionString=[dbname='" + postgres_db_dbname
                        + "' user='" + postgres_db_user + "' host='" + host + "' password='************']")
            postgresConn = psycopg2.connect(dbConnectionString)
            logger.info("[main.py setupDB] PostgreSQL connection established")
            postgresConn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            postgresCurs = postgresConn.cursor()
            # these two parts is using a complicated DO statement because apparently postgres does not have
            # an if not exist" clause for roles or databases, only tables moreover, this is done to localhost
            # and not any other environment cause with the TEST guild, the databases are always brand new
            # fresh with each time the script get launched
            if 'localhost' == env or'PRODUCTION' == env:
                # aquired from https://stackoverflow.com/a/8099557/7734535
                sqlQuery = """DO
                $do$
                BEGIN
                IF NOT EXISTS (
                SELECT                       -- SELECT list can stay empty for this
                FROM   pg_catalog.pg_roles
                WHERE  rolname = '""" + wall_e_db_user + """') THEN
                CREATE ROLE """ + wall_e_db_user + """ WITH NOSUPERUSER INHERIT NOCREATEROLE NOCREATEDB LOGIN
                 NOREPLICATION NOBYPASSRLS ENCRYPTED PASSWORD '""" + wall_e_db_password + """';
                END IF;
                END
                $do$;"""
                postgresCurs.execute(sqlQuery)
            else:
                postgresCurs.execute("CREATE ROLE " + wall_e_db_user + " WITH NOSUPERUSER INHERIT "
                                     "NOCREATEROLE NOCREATEDB LOGIN NOREPLICATION NOBYPASSRLS ENCRYPTED "
                                     "PASSWORD '" + wall_e_db_password + "';")
            logger.info("[main.py setupDB] " + wall_e_db_user + " role created")
            if 'localhost' == env or 'PRODUCTION' == env:
                sqlQuery = """SELECT datname from pg_database"""
                postgresCurs.execute(sqlQuery)
                results = postgresCurs.fetchall()
                # fetchAll returns  [('postgres',), ('template0',), ('template1',), ('csss_discord_db',)]
                # which the below line converts to  ['postgres', 'template0', 'template1', 'csss_discord_db']
                results = [x for xs in results for x in xs]
                if wall_e_db_dbname not in results:
                    postgresCurs.execute("CREATE DATABASE " + wall_e_db_dbname + " WITH OWNER"
                                         " " + wall_e_db_user + " TEMPLATE = template0;")
                    logger.info("[main.py setupDB] " + wall_e_db_dbname + " database created")
                else:
                    logger.info("[main.py setupDB] " + wall_e_db_dbname + " database already exists")
            else:
                postgresCurs.execute("CREATE DATABASE " + wall_e_db_dbname + " WITH OWNER"
                                     " " + wall_e_db_user + " TEMPLATE = template0;")
                logger.info("[main.py setupDB] " + wall_e_db_dbname + " database created")
            # this section exists cause of this backup.sql that I had exported from an instance of a Postgres with
            # which I had created the csss_discord_db
            # https://github.com/CSSS/wall_e/blob/implement_postgres/helper_files/backup.sql#L31
            dbConnectionString = ("dbname='" + wall_e_db_dbname + "' user='" + postgres_db_user + "'"
                                  " host='" + host + "' password='" + postgres_password + "'")
            logger.info("[main.py setupDB] Wall_e User dbConnectionString=[dbname='" + wall_e_db_dbname + "'"
                        " user='" + postgres_db_user + "' host='" + host + "' password='*****']")
            walleConn = psycopg2.connect(dbConnectionString)
            logger.info("[main.py setupDB] PostgreSQL connection established")
            walleConn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            walleCurs = walleConn.cursor()
            walleCurs.execute("SET statement_timeout = 0;")
            walleCurs.execute("SET default_transaction_read_only = off;")
            walleCurs.execute("SET lock_timeout = 0;")
            walleCurs.execute("SET idle_in_transaction_session_timeout = 0;")
            walleCurs.execute("SET client_encoding = 'UTF8';")
            walleCurs.execute("SET standard_conforming_strings = on;")
            walleCurs.execute("SELECT pg_catalog.set_config('search_path', '', false);")
            walleCurs.execute("SET check_function_bodies = false;")
            walleCurs.execute("SET client_min_messages = warning;")
            walleCurs.execute("SET row_security = off;")
            walleCurs.execute("CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;")
            walleCurs.execute("COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';")
        except Exception as e:
            logger.error("[main.py setupDB] enountered following exception when setting up PostgreSQL "
                         "connection\n{}".format(e))


def setupStatsOfCommandsDBTable(config):
    if config.enabled("database"):
        try:
            host = config.get_config_value('basic_config', 'COMPOSE_PROJECT_NAME') + '_wall_e_db'
            dbConnectionString = (
                "dbname='" + config.get_config_value('database', 'WALL_E_DB_DBNAME') + "' "
                "user='" + config.get_config_value('database', 'WALL_E_DB_USER') + "' host='" + host + "' "
                "password='" + config.get_config_value('database', 'WALL_E_DB_PASSWORD') + "'")
            logger.info(
                "[main.py setupStatsOfCommandsDBTable()] dbConnectionString=[dbname='"
                + config.get_config_value('database', 'WALL_E_DB_DBNAME') + "' user="
                "'" + config.get_config_value('database', 'WALL_E_DB_USER') + "' host='" + host
                + "' password='******']"
            )
            conn = psycopg2.connect(dbConnectionString)
            logger.info("[main.py setupStatsOfCommandsDBTable()] PostgreSQL connection established")
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            curs = conn.cursor()
            curs.execute(
                "CREATE TABLE IF NOT EXISTS CommandStats ( \"EPOCH TIME\" BIGINT  PRIMARY KEY, YEAR BIGINT, "
                "MONTH BIGINT, DAY BIGINT, HOUR BIGINT, \"Channel Name\" varchar(2000), "
                "Command varchar(2000), \"Invoked with\" "
                "varchar(2000), \"Invoked subcommand\"  varchar(2000));"
            )
            logger.info("[main.py setupStatsOfCommandsDBTable()] CommandStats database table created")
        except Exception as e:
            logger.error("[main.py setupStatsOfCommandsDBTable()] enountered following exception when setting up "
                         "PostgreSQL connection\n{}".format(e))
