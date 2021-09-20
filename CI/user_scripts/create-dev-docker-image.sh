#!/bin/bash


# PURPOSE: TO BE USED BY THE USER WHEN THEY HAVE MADE CHANGES TO EITHER THE DOCKERFILE.BASE OR REQUIREMENTS FILE
# WHICH MEANS THEY CAN NO LONGE RELY ON THE REPO STORED AT SFUCSSSORG/WALL_E FOR THEIR LOCAL DEV AND NEED TO CREATE THEIR OWN
## DOCKER WALL_E BASE IMAGE TO WORK OFF OF

set -e -o xtrace
# https://stackoverflow.com/a/5750463/7734535

if [ -z "${COMPOSE_PROJECT_NAME}" ]; then
	echo "COMPOSE_PROJECT_NAME needs to be set"
	exit 1
fi

export test_base_image_name_lower_case=$(echo "${COMPOSE_PROJECT_NAME}"_wall_e_base | awk '{print tolower($0)}')
export DOCKERFILE="CI/server_scripts/build_wall_e/Dockerfile.wall_e_base"
export CONTAINER_HOME_DIR="/usr/src/app"

pushd ../../
./CI/destroy-dev-env.sh

docker image rm -f "${test_base_image_name_lower_case}" || true
docker build --no-cache -t ${test_base_image_name_lower_case} -f "${DOCKERFILE}" --build-arg WALL_E_BASE_ORIGIN_NAME="sfucsssorg/wall_e_python" --build-arg CONTAINER_HOME_DIR="${CONTAINER_HOME_DIR}" .
popd