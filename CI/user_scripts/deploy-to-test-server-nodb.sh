#!/bin/bash


# PURPOSE: TO BE USED BY THE USER WHEN THEY WANT TO DEPLOY WALL_E TO THEIR OWN DISCORD GUILD
# WITHOUT THE USE OF A DATABASE


set -e -o xtrace
# https://stackoverflow.com/a/5750463/7734535

if [ -z "${COMPOSE_PROJECT_NAME}" ]; then
	echo "COMPOSE_PROJECT_NAME is not set"
	exit 1
fi

if [ -z "${ORIGIN_IMAGE}" ]; then
	echo "ORIGIN_IMAGE is not set"
	exit 1
fi

export ENVIRONMENT="LOCALHOST"
testContainerDBName="${COMPOSE_PROJECT_NAME}_wall_e_db"
testContainerName="${COMPOSE_PROJECT_NAME}_wall_e"
docker rm -f ${testContainerName} ${testContainerDBName} || true
COMPOSE_PROJECT_NAME_lowerCase=$(echo "$COMPOSE_PROJECT_NAME" | awk '{print tolower($0)}')
testContainerName_lowerCase=$(echo "$testContainerName" | awk '{print tolower($0)}')
docker network rm ${COMPOSE_PROJECT_NAME_lowerCase}_default || true
docker image rm -f ${testContainerName_lowerCase} || true
docker volume create --name="${COMPOSE_PROJECT_NAME}_logs"
docker-compose -f CI/user_scripts/docker-compose-mount-nodb.yml up --force-recreate -d
sleep 20

containerFailed=$(docker ps -a -f name=${testContainerName} --format "{{.Status}}" | head -1)
if [[ "${containerFailed}" != *"Up"* ]]; then
    docker logs ${testContainerName}
    exit 1
fi
