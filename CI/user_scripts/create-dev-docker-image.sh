#!/bin/bash


# PURPOSE: TO BE USED BY THE USER WHEN THEY HAVE MADE CHANGES TO EITHER THE DOCKERFILE.BASE OR REQUIREMENTS FILE
# WHICH MEANS THEY CAN NO LONGE RELY ON THE REPO STORED AT SFUCSSSORG/WALL_E FOR THEIR LOCAL DEV AND NEED TO CREATE THEIR OWN
## DOCKER WALL_E BASE IMAGE TO WORK OFF OF

set -e -o xtrace
# https://stackoverflow.com/a/5750463/7734535

if [ -z "${COMPOSE_PROJECT_NAME}" ]; then
	echo "COMPOSE_PROJECT_NAME is not set"
	exit 1
fi

export testBaseImageName_lowerCase=$(echo "${COMPOSE_PROJECT_NAME}"_wall_e_base | awk '{print tolower($0)}')
export testWallEImageName_lowerCase=$(echo "${COMPOSE_PROJECT_NAME}"_wall_e | awk '{print tolower($0)}')
export testWallEContainer="${COMPOSE_PROJECT_NAME}"_wall_e
export DOCKERFILE="CI/server_scripts/build_wall_e/Dockerfile.wall_e_base"
export CONTAINER_HOME_DIR="/usr/src/app"

docker stop "${testWallEContainer}" || true
docker rm "${testWallEContainer}" || true
docker image rm -f "${testBaseImageName_lowerCase}" "${testWallEImageName_lowerCase}" || true
docker build --no-cache -t ${testBaseImageName_lowerCase} -f "${DOCKERFILE}" --build-arg CONTAINER_HOME_DIR="${CONTAINER_HOME_DIR}" .
