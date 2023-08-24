#!/bin/sh
# wait-for-postgres.sh

# aquired from https://docs.docker.com/compose/startup-order/
set -e -o xtrace

cmd="$@"

until PGPASSWORD=$database_config__WALL_E_DB_PASSWORD psql -h "db" \
   -U "${database_config__WALL_E_DB_USER}" -d "${database_config__WALL_E_DB_DBNAME}" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"

exec $cmd

