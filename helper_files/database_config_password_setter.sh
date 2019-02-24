#!/bin/bash

if [[ "$ENVIRONMENT" == 'localhost' ]]; then
	#postgresLine="ALTER ROLE postgres WITH SUPERUSER INHERIT CREATEROLE CREATEDB LOGIN REPLICATION BYPASSRLS PASSWORD '${POSTGRES_DB_PASSWORD_HASH}';"
	walleLine="ALTER ROLE wall_e WITH NOSUPERUSER INHERIT NOCREATEROLE NOCREATEDB LOGIN NOREPLICATION NOBYPASSRLS PASSWORD '${WALL_E_DB_PASSWORD_HASH}';"

	DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
	cd $DIR/../
	pwd

	cp helper_files/backup.sql local_development/backup.sql
	#sed -i '/ALTER ROLE postgres WITH SUPERUSER INHERIT CREATEROLE CREATEDB LOGIN REPLICATION BYPASSRLS PASSWORD/c\'"$postgresLine" local_development/backup.sql
	sed -i '/ALTER ROLE wall_e WITH NOSUPERUSER INHERIT NOCREATEROLE NOCREATEDB LOGIN NOREPLICATION NOBYPASSRLS PASSWORD/c\'"$walleLine" local_development/backup.sql
	#sudo cp local_development/backup.sql ~postgres/backup.sql
	#sudo -iu postgres
	psql -U postgres -f local_development/backup.sql postgres
elif [[ "$ENVIRONMENT" == 'TEST' ]] || [[ "$ENVIRONMENT" == 'PRODUCTION' ]]; then
	postgresLine="ALTER ROLE postgres WITH SUPERUSER INHERIT CREATEROLE CREATEDB LOGIN REPLICATION BYPASSRLS PASSWORD '${POSTGRES_DB_PASSWORD_HASH}';"
	walleLine="ALTER ROLE wall_e WITH NOSUPERUSER INHERIT NOCREATEROLE NOCREATEDB LOGIN NOREPLICATION NOBYPASSRLS PASSWORD '${WALL_E_DB_PASSWORD_HASH}';"

	DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
	cd $DIR/../
	pwd

	sed -i '/ALTER ROLE postgres WITH SUPERUSER INHERIT CREATEROLE CREATEDB LOGIN REPLICATION BYPASSRLS PASSWORD/c\'"$postgresLine" ${DIR}/database_config_file/backup.sql
	sed -i '/ALTER ROLE wall_e WITH NOSUPERUSER INHERIT NOCREATEROLE NOCREATEDB LOGIN NOREPLICATION NOBYPASSRLS PASSWORD/c\'"$walleLine" ${DIR}/database_config_file/backup.sql
fi