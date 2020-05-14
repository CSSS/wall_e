import logging


logger = logging.getLogger('wall_e')


###############################
# SETUP DATABASE CONNECTION ##
###############################
def setup_database(config):
    if config.enabled("database", option="DB_ENABLED"):
        try:
            import psycopg2
            env = config.get_config_value("basic_config", "ENVIRONMENT")
            compose_project_name = config.get_config_value("basic_config", "COMPOSE_PROJECT_NAME")
            postgres_db_dbname = config.get_config_value("database", "POSTGRES_DB_DBNAME")
            postgres_db_user = config.get_config_value("database", "POSTGRES_DB_USER")
            postgres_password = config.get_config_value("database", "POSTGRES_PASSWORD")
            wall_e_db_dbname = config.get_config_value("database", "WALL_E_DB_DBNAME")
            wall_e_db_user = config.get_config_value("database", "WALL_E_DB_USER")
            wall_e_db_password = config.get_config_value("database", "WALL_E_DB_PASSWORD")

            host = '{}_wall_e_db'.format(compose_project_name)
            db_connection_string = (
                "dbname='{}' user='{}' host='{}'".format(postgres_db_dbname, postgres_db_user, host)
            )
            logger.info(
                "[database.py setup_database] "
                "Postgres User db_connection_string=[{}]".format(db_connection_string)
            )
            postgres_conn = psycopg2.connect("{} password='{}'".format(db_connection_string, postgres_password))
            logger.info("[database.py setup_database] PostgreSQL connection established")
            postgres_conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            postgres_curs = postgres_conn.cursor()
            # these two parts is using a complicated DO statement because apparently postgres does not have
            # an if not exist" clause for roles or databases, only tables moreover, this is done to localhost
            # and not any other environment cause with the TEST guild, the databases are always brand new
            # fresh with each time the script get launched
            if 'localhost' == env or 'PRODUCTION' == env:
                # aquired from https://stackoverflow.com/a/8099557/7734535
                sql_query = """DO
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
                postgres_curs.execute(sql_query)
            else:
                postgres_curs.execute("CREATE ROLE {} WITH NOSUPERUSER INHERIT "
                                      "NOCREATEROLE NOCREATEDB LOGIN NOREPLICATION NOBYPASSRLS ENCRYPTED "
                                      "PASSWORD '{}';".format(wall_e_db_user, wall_e_db_password))
            logger.info("[database.py setup_database] {} role created".format(wall_e_db_user))
            if 'localhost' == env or 'PRODUCTION' == env:
                sql_query = """SELECT datname from pg_database"""
                postgres_curs.execute(sql_query)
                results = postgres_curs.fetchall()
                # fetchAll returns  [('postgres',), ('template0',), ('template1',), ('csss_discord_db',)]
                # which the below line converts to  ['postgres', 'template0', 'template1', 'csss_discord_db']
                results = [x for xs in results for x in xs]
                if wall_e_db_dbname not in results:
                    postgres_curs.execute(
                        "CREATE DATABASE {} WITH OWNER {} TEMPLATE = template0;".format(
                            wall_e_db_dbname,
                            wall_e_db_user
                        )
                    )
                    logger.info("[database.py setup_database] {} database created".format(wall_e_db_dbname))
                else:
                    logger.info("[database.py setup_database] {} database already exists".format(wall_e_db_dbname))
            else:
                postgres_curs.execute(
                    "CREATE DATABASE {} WITH OWNER {} TEMPLATE = template0;".format(
                        wall_e_db_dbname,
                        wall_e_db_user
                    )
                )
                logger.info("[database.py setup_database] {} database created".format(wall_e_db_dbname))
            # this section exists cause of this backup.sql that I had exported from an instance of a Postgres with
            # which I had created the csss_discord_db
            # https://github.com/CSSS/wall_e/blob/19d5d7a32f4e4188d05895c5f7005efa258a5d20/helper_files/backup.sql#L31
            db_connection_string = ("dbname='{}' user='{}' host='{}'".format(wall_e_db_dbname, wall_e_db_user, host))
            logger.info("[database.py setup_database] Wall_e User db_connection_string=[{}]".format(
                db_connection_string)
            )
            walle_conn = psycopg2.connect("{} password='{}'".format(db_connection_string, wall_e_db_password))
            logger.info("[database.py setup_database] PostgreSQL connection established")
            walle_conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            walle_curs = walle_conn.cursor()
            walle_curs.execute("SET statement_timeout = 0;")
            walle_curs.execute("SET default_transaction_read_only = off;")
            walle_curs.execute("SET lock_timeout = 0;")
            walle_curs.execute("SET idle_in_transaction_session_timeout = 0;")
            walle_curs.execute("SET client_encoding = 'UTF8';")
            walle_curs.execute("SET standard_conforming_strings = on;")
            walle_curs.execute("SELECT pg_catalog.set_config('search_path', '', false);")
            walle_curs.execute("SET check_function_bodies = false;")
            walle_curs.execute("SET client_min_messages = warning;")
            walle_curs.execute("SET row_security = off;")
            walle_curs.execute("CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;")
            # walle_curs.execute("COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';")
        except Exception as e:
            logger.error("[database.py setup_database] enountered following exception when setting up PostgreSQL "
                         "connection\n{}".format(e))


def setup_stats_of_command_database_table(config):
    if config.enabled("database", option="DB_ENABLED"):
        try:
            import psycopg2
            host = '{}_wall_e_db'.format(config.get_config_value('basic_config', 'COMPOSE_PROJECT_NAME'))
            db_connection_string = ("dbname='{}' user='{}' host='{}' ".format(
                    config.get_config_value('database', 'WALL_E_DB_DBNAME'),
                    config.get_config_value('database', 'WALL_E_DB_USER'),
                    host
                ))
            logger.info(
                "[database.py setup_stats_of_command_database_table()] "
                "db_connection_string=[{}]".format(db_connection_string)
            )
            conn = psycopg2.connect(
                "{} password='{}'".format(
                    db_connection_string,
                    config.get_config_value('database', 'WALL_E_DB_PASSWORD')
                )
            )
            logger.info("[database.py setup_stats_of_command_database_table()] PostgreSQL connection established")
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            curs = conn.cursor()
            curs.execute(
                "CREATE TABLE IF NOT EXISTS CommandStats ( epoch_time BIGINT  PRIMARY KEY, YEAR BIGINT, "
                "MONTH BIGINT, DAY BIGINT, HOUR BIGINT, channel_name varchar(2000), "
                "Command varchar(2000), invoked_with "
                "varchar(2000), invoked_subcommand  varchar(2000));"
            )
            logger.info("[database.py setup_stats_of_command_database_table()] CommandStats database table created")
        except Exception as e:
            logger.error(
                "[database.py setup_stats_of_command_database_table()] enountered "
                "following exception when setting up "
                "PostgreSQL connection\n{}".format(e)
            )
