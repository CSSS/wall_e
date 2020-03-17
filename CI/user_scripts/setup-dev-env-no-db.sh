#!/bin/bash


# PURPOSE: TO BE USED BY THE USER WHEN THEY WANT TO DEPLOY WALL_E TO THEIR OWN DISCORD GUILD
# WITHOUT THE USE OF A DATABASE


set -e -o xtrace
# https://stackoverflow.com/a/5750463/7734535

if [ -z "${COMPOSE_PROJECT_NAME}" ]; then
	echo "COMPOSE_PROJECT_NAME needs to be set"
	exit 1
fi

if [ -z "${ORIGIN_IMAGE}" ]; then
	echo "ORIGIN_IMAGE needs to be set"
	exit 1
fi

./CI/destroy-dev-env.sh

docker volume create --name="${COMPOSE_PROJECT_NAME}_logs"
export ENVIRONMENT="LOCALHOST"
export DB_ENABLED="0"
docker-compose -f CI/user_scripts/docker-compose-mount-nodb.yml up --force-recreate -d

sleep 20
wall_e_container_name="${COMPOSE_PROJECT_NAME}_wall_e"
containerFailed=$(docker ps -a -f name="${wall_e_container_name}" --format "{{.Status}}" | head -1)
if [[ "${containerFailed}" != *"Up"* ]]; then
    docker logs "${wall_e_container_name}"
    exit 1
fi

echo "wall_e succesfully launched!"
