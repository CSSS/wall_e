#!/bin/bash

# PURPOSE: used be jenkins to launch a branch's version of wall_e to the CSSS Staging Discord Guild

set -e -o xtrace
# https://stackoverflow.com/a/5750463/7734535

# required if the docker image needs to be created and cannot just use sfucsssorg/wall_e
if [ -z "${BRANCH_NAME}" ]; then
    echo "BRANCH_NAME is not set"
    exit 1
fi

rm ${DISCORD_NOTIFICATION_MESSAGE_FILE} || true

# the names of the container and docker-compose file used for wall_e that is running under the current `COMPOSE_PROJECT_NAME`
export test_container_db_name="${COMPOSE_PROJECT_NAME}_wall_e_db"
export test_container_name="${COMPOSE_PROJECT_NAME}_wall_e"
export compose_project_name=$(echo "$COMPOSE_PROJECT_NAME" | awk '{print tolower($0)}')
export test_image_name=$(echo "${test_container_name}" | awk '{print tolower($0)}')
export docker_compose_file="CI/server_scripts/build_wall_e/docker-compose-master.yml"


# the name of the docker image that will get assigned to the foundational images that are created or used if one of the tracked
# files are changed
export wall_e_top_base_image=$(echo "${COMPOSE_PROJECT_NAME}_wall_e_base_image" | awk '{print tolower($0)}')

# the tracked files
export wall_e_top_base_image_dockerfile="CI/server_scripts/build_wall_e/Dockerfile.wall_e_base"

touch CI/user_scripts/wall_e.env
./CI/destroy-dev-env.sh
rm CI/user_scripts/wall_e.env


# handles creating the waLl_e base image
# will result in the origin name for the wall_e image to be set to either "sfucsssorg/wall_e" [if no change is needed] or $wall_e_top_base_image [if the image had to be built]
re_create_top_base_image () {
    docker stop "${test_container_db_name}" "${test_container_name}" || true
    docker rm "${test_container_db_name}" "${test_container_name}"|| true
    docker image rm -f "${test_image_name}" "${wall_e_top_base_image}" || true
    docker build --no-cache -t ${wall_e_top_base_image} -f ${wall_e_top_base_image_dockerfile} \
    --build-arg CONTAINER_HOME_DIR=${CONTAINER_HOME_DIR} \
    --build-arg WALL_E_BASE_ORIGIN_NAME="sfucsssorg/wall_e_python" .
  }

re_create_top_base_image

export ORIGIN_IMAGE="${wall_e_top_base_image}"

docker volume create --name="${COMPOSE_PROJECT_NAME}_logs"

docker-compose -f "${docker_compose_file}" up --force-recreate  -d
sleep 60

export container_failed=$(docker ps -a -f name=${test_container_name} --format "{{.Status}}" | head -1)
export container_db_failed=$(docker ps -a -f name=${test_container_db_name} --format "{{.Status}}" | head -1)
if [[ "${container_failed}" != *"Up"* ]]; then
    docker logs ${test_container_name}
    docker logs ${test_container_name} --tail 12 &> ${DISCORD_NOTIFICATION_MESSAGE_FILE}
    exit 1
fi

if [[ "${container_db_failed}" != *"Up"* ]]; then
    docker logs ${test_container_db_name}
    docker logs ${test_container_db_name} --tail 12 &> ${DISCORD_NOTIFICATION_MESSAGE_FILE}
    exit 1
fi
