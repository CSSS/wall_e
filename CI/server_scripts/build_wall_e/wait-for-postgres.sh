#!/bin/sh
# wait-for-postgres.sh

# aquired from https://docs.docker.com/compose/startup-order/
set -e

host="$1"
shift
cmd="$@"

until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$host" -U "postgres" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"

PGPASSWORD=$POSTGRES_PASSWORD psql --set=WALL_E_DB_USER="${WALL_E_DB_USER}" \
  --set=WALL_E_DB_PASSWORD="${WALL_E_DB_PASSWORD}"  --set=WALL_E_DB_DBNAME="${WALL_E_DB_DBNAME}" \
  -h "$host" -U "postgres" -f WalleModels/create-database.ddl

python3 django_db_orm_manage.py migrate

if [ "$ENVIRONMENT" != "PRODUCTION" ]; then
  rm wall_e.json || true
  wget https://dev.sfucsss.org/dev_csss_wall_e/fixtures/wall_e.json
  python3 django_db_orm_manage.py loaddata wall_e.json

  mv WalleModels/staging_migrations/*.py WalleModels/migrations/. || true
  python3 django_db_orm_manage.py migrate
fi

exec $cmd

