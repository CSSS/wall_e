#!/bin/bash


## PURPOSE: intended to be used by jenkins whenever it needs to re-create the base docker image for a master branch

set -e -o xtrace
# https://stackoverflow.com/a/5750463/7734535

if [ -z "${DOCKER_HUB_PASSWORD}" ]; then
    echo "DOCKER_HUB_PASSWORD is not set"
    exit 1
fi


if [ -z "${DOCKER_HUB_USER_NAME}" ]; then
    echo "DOCKER_HUB_USER_NAME is not set"
    exit 1
fi


export docker_registry="sfucsssorg"
export wall_e_top_base_image="wall_e_base"
export WALL_E_BASE_IMAGE="${docker_registry}/wall_e"
export WALL_E_PYTHON_BASE_IMAGE="${docker_registry}/wall_e_python"

export test_container_db_name="${COMPOSE_PROJECT_NAME}_wall_e_db"
export test_container_name="${COMPOSE_PROJECT_NAME}_wall_e"
export test_image_name=$(echo "${COMPOSE_PROJECT_NAME}_wall_e" | awk '{print tolower($0)}')

export wall_e_top_base_image_dockerfile="CI/server_scripts/build_wall_e/Dockerfile.wall_e_base"

re_create_top_base_image () {
    docker stop "${test_container_db_name}" "${test_container_name}" || true
    docker rm "${test_container_db_name}" "${test_container_name}" || true
    docker image rm -f "${test_image_name}" "${wall_e_top_base_image}" "${WALL_E_BASE_IMAGE}" || true
    docker build --no-cache -t ${wall_e_top_base_image} -f ${wall_e_top_base_image_dockerfile} \
    --build-arg CONTAINER_HOME_DIR=${CONTAINER_HOME_DIR} \
    --build-arg WALL_E_BASE_ORIGIN_NAME=${WALL_E_PYTHON_BASE_IMAGE} .
    docker tag ${wall_e_top_base_image} ${WALL_E_BASE_IMAGE}
    echo "${DOCKER_HUB_PASSWORD}" | docker login --username=${DOCKER_HUB_USER_NAME} --password-stdin
    docker push ${WALL_E_BASE_IMAGE}
    docker image rm "${wall_e_top_base_image}" "${WALL_E_BASE_IMAGE}"
    exit 0
}

re_create_top_base_image

exit 0
