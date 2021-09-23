#!/bin/bash


# PURPOSE: TO BE USED BY THE USER WHEN THEY WANT TO DEPLOY WALL_E TO THEIR OWN DISCORD GUILD
# WITH THE USE OF A DATABASE


set -e -o xtrace
# https://stackoverflow.com/a/5750463/7734535

if [ -z "${COMPOSE_PROJECT_NAME}" ]; then
	echo "COMPOSE_PROJECT_NAME needs to be set"
	exit 1
fi

if [ -z "${POSTGRES_PASSWORD}" ]; then
	echo "POSTGRES_PASSWORD needs to be set"
	exit 1
fi

if [ -z "${ORIGIN_IMAGE}" ]; then
	echo "ORIGIN_IMAGE needs to be set"
	exit 1
fi

pushd ../../

./CI/destroy-dev-env.sh

docker volume create --name="${COMPOSE_PROJECT_NAME}_logs"
docker-compose -f CI/user_scripts/docker-compose-mount.yml up --force-recreate -d
popd

wall_e_container_name="${COMPOSE_PROJECT_NAME}_wall_e"
wall_e_db_container_name="${COMPOSE_PROJECT_NAME}_wall_e_db"

while [ "$(docker inspect -f '{{.State.Running}}' ${wall_e_db_container_name})" != "true" ]
do
	echo "waiting for wall_e's database to launch"
	sleep 1
done

while [ "$(docker inspect -f '{{.State.Running}}' ${wall_e_container_name})"  != "true" ]
do
	echo "waiting for wall_e to launch"
	sleep 1
done

echo "wall_e with database succesfully launched!"
