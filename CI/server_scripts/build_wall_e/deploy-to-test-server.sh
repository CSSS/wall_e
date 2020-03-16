#!/bin/bash

# PURPOSE: used be jenkins to launch Wall_e to the CSSS TEST Discord Guild

set -e -o xtrace
# https://stackoverflow.com/a/5750463/7734535

rm ${DISCORD_NOTIFICATION_MESSAGE_FILE} || true

export test_container_db_name="${COMPOSE_PROJECT_NAME}_wall_e_db"
export test_container_name="${COMPOSE_PROJECT_NAME}_wall_e"
export test_image_name_lower_case=$(echo "$test_container_name" | awk '{print tolower($0)}')
export compose_project_name_lower_case=$(echo "$COMPOSE_PROJECT_NAME" | awk '{print tolower($0)}')
export docker_compose_file="CI/server_scripts/build_wall_e/docker-compose.yml"
export ORIGIN_IMAGE="sfucsssorg/wall_e"


docker rm -f ${test_container_name} ${test_container_db_name} || true
docker network rm ${compose_project_name_lower_case}_default || true
docker image rm -f ${test_image_name_lower_case} || true
docker volume create --name="${COMPOSE_PROJECT_NAME}_logs"

docker-compose -f "${docker_compose_file}" up --force-recreate  -d
sleep 20

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
