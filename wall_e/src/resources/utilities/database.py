import logging
import psycopg2

logger = logging.getLogger('wall_e')


###############################
# SETUP DATABASE CONNECTION ##
###############################
def setupDB(config):
    if config.enabled("database", option="DB_ENABLED"):
        try:
            env = config.get_config_value("wall_e", "ENVIRONMENT")
            compose_project_name = config.get_config_value("wall_e", "COMPOSE_PROJECT_NAME")
            postgres_db_dbname = config.get_config_value("database", "POSTGRES_DB_DBNAME")
            postgres_db_user = config.get_config_value("database", "POSTGRES_DB_USER")
            postgres_password = config.get_config_value("database", "POSTGRES_PASSWORD")
            wall_e_db_dbname = config.get_config_value("database", "WALL_E_DB_DBNAME")
            wall_e_db_user = config.get_config_value("database", "WALL_E_DB_USER")
            wall_e_db_password = config.get_config_value("database", "WALL_E_DB_PASSWORD")

            host = '{}_wall_e_db'.format(compose_project_name)
            dbConnectionString = (
                "dbname='{}' user='{}' host='{}'".format(postgres_db_dbname, postgres_db_user, host)
            )
            logger.info("[database.py setupDB] Postgres User dbConnectionString=[{}]".format(dbConnectionString))
            postgresConn = psycopg2.connect("{} password='{}'".format(dbConnectionString, postgres_password))
            logger.info("[database.py setupDB] PostgreSQL connection established")
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
                postgresCurs.execute("CREATE ROLE {} WITH NOSUPERUSER INHERIT "
                                     "NOCREATEROLE NOCREATEDB LOGIN NOREPLICATION NOBYPASSRLS ENCRYPTED "
                                     "PASSWORD '{}';".format(wall_e_db_user, wall_e_db_password))
            logger.info("[database.py setupDB] {} role created".format(wall_e_db_user))
            if 'localhost' == env or 'PRODUCTION' == env:
                sqlQuery = """SELECT datname from pg_database"""
                postgresCurs.execute(sqlQuery)
                results = postgresCurs.fetchall()
                # fetchAll returns  [('postgres',), ('template0',), ('template1',), ('csss_discord_db',)]
                # which the below line converts to  ['postgres', 'template0', 'template1', 'csss_discord_db']
                results = [x for xs in results for x in xs]
                if wall_e_db_dbname not in results:
                    postgresCurs.execute(
                        "CREATE DATABASE {} WITH OWNER {} TEMPLATE = template0;".format(
                            wall_e_db_dbname,
                            wall_e_db_user
                        )
                    )
                    logger.info("[database.py setupDB] {} database created".format(wall_e_db_dbname))
                else:
                    logger.info("[database.py setupDB] {} database already exists".format(wall_e_db_dbname))
            else:
                postgresCurs.execute(
                    "CREATE DATABASE {} WITH OWNER {} TEMPLATE = template0;".format(
                        wall_e_db_dbname,
                        wall_e_db_user
                    )
                )
                logger.info("[database.py setupDB] {} database created".format(wall_e_db_dbname))
            # this section exists cause of this backup.sql that I had exported from an instance of a Postgres with
            # which I had created the csss_discord_db
            # https://github.com/CSSS/wall_e/blob/implement_postgres/helper_files/backup.sql#L31
            dbConnectionString = ("dbname='{}' user='{}' host='{}'".format(wall_e_db_dbname, wall_e_db_user, host))
            logger.info("[database.py setupDB] Wall_e User dbConnectionString=[{}]".format(dbConnectionString))
            walleConn = psycopg2.connect("{} password='{}'".format(dbConnectionString, wall_e_db_password))
            logger.info("[database.py setupDB] PostgreSQL connection established")
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
            # walleCurs.execute("COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';")
        except Exception as e:
            logger.error("[database.py setupDB] enountered following exception when setting up PostgreSQL "
                         "connection\n{}".format(e))


def setupStatsOfCommandsDBTable(config):
    if config.enabled("database", option="DB_ENABLED"):
        try:
            host = '{}_wall_e_db'.format(config.get_config_value('basic_config', 'COMPOSE_PROJECT_NAME'))
            dbConnectionString = ("dbname='{}' user='{}' host='{}' ".format(
                    config.get_config_value('database', 'WALL_E_DB_DBNAME'),
                    config.get_config_value('database', 'WALL_E_DB_USER'),
                    host
                ))
            logger.info(
                "[database.py setupStatsOfCommandsDBTable()] dbConnectionString=[{}]".format(dbConnectionString)
            )
            conn = psycopg2.connect(
                "{} password='{}'".format(
                    dbConnectionString,
                    config.get_config_value('database', 'WALL_E_DB_PASSWORD')
                )
            )
            logger.info("[database.py setupStatsOfCommandsDBTable()] PostgreSQL connection established")
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            curs = conn.cursor()
            curs.execute(
                "CREATE TABLE IF NOT EXISTS CommandStats ( epoch_time BIGINT  PRIMARY KEY, YEAR BIGINT, "
                "MONTH BIGINT, DAY BIGINT, HOUR BIGINT, channel_name varchar(2000), "
                "Command varchar(2000), invoked_with "
                "varchar(2000), invoked_subcommand  varchar(2000));"
            )
            logger.info("[database.py setupStatsOfCommandsDBTable()] CommandStats database table created")
        except Exception as e:
            logger.error("[database.py setupStatsOfCommandsDBTable()] enountered following exception when setting up "
                         "PostgreSQL connection\n{}".format(e))
