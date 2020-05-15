#!/bin/bash

set -e -x
# https://stackoverflow.com/a/5750463/7734535

if [ -z "${COMPOSE_PROJECT_NAME}" ]; then
	echo "COMPOSE_PROJECT_NAME needs to be set"
	exit 1
fi

export image_name=$(echo "${COMPOSE_PROJECT_NAME}"_wall_e | awk '{print tolower($0)}')
export network_name=$(echo "${COMPOSE_PROJECT_NAME}"_default | awk '{print tolower($0)}')
export volume_name="${COMPOSE_PROJECT_NAME}_logs"


pushd CI/user_scripts
cp docker-compose-mount.yml docker-compose.yml
docker-compose rm -f -s -v || true
docker volume rm "${volume_name}" || true
docker image rm "${image_name}" || true
docker network rm "${network_name}" || true
rm docker-compose.yml
popd
