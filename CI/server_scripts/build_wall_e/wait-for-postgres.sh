#!/bin/sh
# wait-for-postgres.sh

# aquired from https://docs.docker.com/compose/startup-order/
set -e -o xtrace

host="$1"
shift
cmd="$@"

until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$host" -U "postgres" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"

HOME_DIR=`pwd`
BRANCH_PREFIX=`echo "${BRANCH_NAME}" | cut -c1-3`
if [[ "${BRANCH_PREFIX}" == "PR-" ]]; then
  rm -r /wall_e || true
  git clone https://github.com/CSSS/wall_e.git /wall_e
  cd /wall_e/wall_e/src/
  PGPASSWORD=$POSTGRES_PASSWORD psql --set=WALL_E_DB_USER="${WALL_E_DB_USER}" \
    --set=WALL_E_DB_PASSWORD="${WALL_E_DB_PASSWORD}"  --set=WALL_E_DB_DBNAME="${WALL_E_DB_DBNAME}" \
    -h "$host" -U "postgres" -f WalleModels/create-database.ddl
fi

python3 django_db_orm_manage.py migrate

#BRANCH_NAME=PR-379
if [[ "${BRANCH_PREFIX}" == "PR-" ]]; then
  wget https://dev.sfucsss.org/dev_csss_wall_e/fixtures/wall_e.json
  python3 django_db_orm_manage.py loaddata wall_e.json
  cd "${HOME_DIR}"
  python3 django_db_orm_manage.py migrate
  rm -r /wall_e || true
fi
## making a separate script for prod that is what this originally was

exec $cmd

