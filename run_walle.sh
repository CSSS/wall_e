#!/bin/bash

#set -e -o xtrace
# https://stackoverflow.com/a/5750463/7734535

if [ -z "${VIRTUAL_ENV}" ]; then
	echo "please active a python virtual environment before using this script"
	exit 1
fi

# need to delete and re-create so that the if statement that tries to detected if the
# help menu was invoked can work correctly
cat ./CI/validate_and_deploy/2_deploy/user_scripts/run_wall_e.env | grep -v HELP_SELECTED > ./CI/validate_and_deploy/2_deploy/user_scripts/run_wall_e.env.2
mv ./CI/validate_and_deploy/2_deploy/user_scripts/run_wall_e.env.2 ./CI/validate_and_deploy/2_deploy/user_scripts/run_wall_e.env

./.run_walle.py $@

while [ "$#" -gt 0 ]
do
    shift
done

. ./CI/validate_and_deploy/2_deploy/user_scripts/set_env.sh
. ./CI/validate_and_deploy/2_deploy/user_scripts/set_env.sh run_wall_e.env

if [ -z "${HELP_SELECTED}" ]; then
	exit 0
fi

if [[ "${basic_config__DOCKERIZED}" == "1" ]]; then
	export COMPOSE_PROJECT_NAME="${basic_config__COMPOSE_PROJECT_NAME}"
	./CI/validate_and_deploy/2_deploy/user_scripts/setup-dev-env.sh
	docker logs -f "${COMPOSE_PROJECT_NAME}_wall_e"
else
	pushd wall_e
	if [ -f 'wall_e_models' ]; then
		ln -sn "${WALL_E_MODEL_PATH}/wall_e_models" wall_e_models
	fi

	if [[ "${INSTALL_REQUIREMENTS}" == "True" ]]; then
		rm layer-1-requirements.txt layer-2-requirements.txt || true
		wget https://raw.githubusercontent.com/CSSS/wall_e_python_base/master/layer-1-requirements.txt
		wget https://raw.githubusercontent.com/CSSS/wall_e_python_base/master/layer-2-requirements.txt
		python3 -m pip install -r layer-1-requirements.txt
		python3 -m pip install -r layer-2-requirements.txt
		rm layer-1-requirements.txt layer-2-requirements.txt
		python3 -m pip install -r requirements.txt
	fi

	if [[ "${SETUP_DATABASE}" == "True" ]]; then
		if [[ "${database_config__TYPE}" == "sqlite3" ]]; then
			rm ../db.sqlite3 || true
		else
			dpkg -s postgresql-contrib &> /dev/null
			if [[ $? -eq 1 ]];
			then
				sudo apt-get install postgresql-contrib
			fi
			docker rm -f "${basic_config__COMPOSE_PROJECT_NAME}_wall_e_db"
			sleep 4
			docker run -d --env POSTGRES_PASSWORD=${POSTGRES_PASSWORD} -p \
			"${database_config__DB_PORT}":5432 --name "${basic_config__COMPOSE_PROJECT_NAME}_wall_e_db" \
			postgres:alpine
			sleep 4
			PGPASSWORD=$POSTGRES_PASSWORD psql --set=WALL_E_DB_USER="${database_config__WALL_E_DB_USER}" \
			--set=WALL_E_DB_PASSWORD="${database_config__WALL_E_DB_PASSWORD}"  \
			--set=WALL_E_DB_DBNAME="${database_config__WALL_E_DB_DBNAME}" \
			-h "${database_config__HOST}" -p "${database_config__DB_PORT}"  -U "postgres" \
			-f ../CI/validate_and_deploy/2_deploy/create-database.ddl
		fi
		python3 django_manage.py migrate
		rm wall_e.json* || true
		wget https://dev.sfucsss.org/wall_e/fixtures/wall_e.json
		python3 django_manage.py loaddata wall_e.json
		rm wall_e.json* || true
	fi
	popd

fi
if [[ "${LAUNCH_WALL_E}" == "True" ]]; then
	echo "Launching the wall_e."
	sleep 3
	cd wall_e
	python3 main.py
fi