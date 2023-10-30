#!/bin/bash
. ./CI/user_scripts/set_env.sh
pushd wall_e
docker rm -f "${basic_config__COMPOSE_PROJECT_NAME}_wall_e_db"
sleep 4
echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}"
docker run -d --env POSTGRES_PASSWORD=${POSTGRES_PASSWORD} -p \
"${database_config__DB_PORT}":5432 --name "${basic_config__COMPOSE_PROJECT_NAME}_wall_e_db" \
postgres:alpine
sleep 4
PGPASSWORD=$POSTGRES_PASSWORD psql --set=WALL_E_DB_USER="${database_config__WALL_E_DB_USER}" \
--set=WALL_E_DB_PASSWORD="${database_config__WALL_E_DB_PASSWORD}"  \
--set=WALL_E_DB_DBNAME="${database_config__WALL_E_DB_DBNAME}" \
-h "${database_config__HOST}" -p "${database_config__DB_PORT}"  -U "postgres" \
-f ../CI/create-database.ddl
python3 django_manage.py migrate
rm wall_e.json* || true
wget https://dev.sfucsss.org/wall_e/fixtures/wall_e.json
python3 django_manage.py loaddata wall_e.json
rm wall_e.json* || true
popd