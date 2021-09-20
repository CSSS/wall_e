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

PGPASSWORD=$POSTGRES_PASSWORD psql -h "$host" -U "postgres" -f WalleModels/create-database.ddl

python3 django-db-orm-manage.py makemigrations
python3 django-db-orm-manage.py migrate

exec $cmd

