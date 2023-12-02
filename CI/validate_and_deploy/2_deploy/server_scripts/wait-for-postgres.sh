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

if [[ "${basic_config__ENVIRONMENT}" == "TEST" ]]; then
	# setup database
	HOME_DIR=`pwd`
	rm -r /wall_e || true
	git clone https://github.com/CSSS/wall_e.git /wall_e
	cd /wall_e/wall_e/
	PGPASSWORD=$POSTGRES_PASSWORD psql --set=WALL_E_DB_USER="${database_config__WALL_E_DB_USER}" \
	--set=WALL_E_DB_PASSWORD="${database_config__WALL_E_DB_PASSWORD}" \
	--set=WALL_E_DB_DBNAME="${database_config__WALL_E_DB_DBNAME}" \
	-h "$host" -U "postgres" -f "${HOME_DIR}"/create-database.ddl
	python3 -m pip install -r ../CI/validate_and_deploy/2_deploy/server_scripts/wall_e_models_requirement.txt
	python3 django_manage.py migrate
	wget -r --no-parent -nd https://dev.sfucsss.org/wall_e/fixtures/ -A 'json'
	python3 django_manage.py loaddata banrecords.json
	python3 django_manage.py loaddata commandstats.json
	python3 django_manage.py loaddata levels.json
	python3 django_manage.py loaddata profilebucketsinprogress.json
	python3 django_manage.py loaddata reminders.json
	python3 django_manage.py loaddata userpoints.json
	rm banrecords.json commandstats.json levels.json profilebucketsinprogress.json reminders.json userpoints.json
	cd "${HOME_DIR}"
	rm -r /wall_e || true
fi

python3 -m pip install -r wall_e_models_requirement.txt
python3 django_manage.py migrate

exec $cmd

