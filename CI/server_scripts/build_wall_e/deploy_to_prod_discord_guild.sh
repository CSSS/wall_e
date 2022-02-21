#!/bin/bash

# PURPOSE: used be jenkins to launch Wall_e to the CSSS PROD Discord Guild

set -e -o xtrace
# https://stackoverflow.com/a/5750463/7734535

rm ${DISCORD_NOTIFICATION_MESSAGE_FILE} || true

export prod_container_name="${COMPOSE_PROJECT_NAME}_wall_e"
export prod_container_db_name="${COMPOSE_PROJECT_NAME}_wall_e_db"
export prod_container_web_name="${COMPOSE_PROJECT_NAME}_wall_e_web"
export docker_compose_file="CI/server_scripts/build_wall_e/docker-compose.yml"
export compose_project_name=$(echo "$COMPOSE_PROJECT_NAME" | awk '{print tolower($0)}')
export prod_image_name_lower_case=$(echo "$prod_container_name" | awk '{print tolower($0)}')
export prod_image_web_name_lower_case=$(echo "$prod_container_web_name" | awk '{print tolower($0)}')
export ORIGIN_IMAGE="sfucsssorg/wall_e"


docker rm -f ${prod_container_name} || true
docker rm -f ${prod_container_web_name} || true
docker image rm -f ${prod_image_name_lower_case} || true
docker image rm -f ${prod_image_web_name_lower_case} || true
docker volume create --name="${COMPOSE_PROJECT_NAME}_logs"
docker-compose -f "${docker_compose_file}" up -d
sleep 20

container_failed=$(docker ps -a -f name=${prod_container_name} --format "{{.Status}}" | head -1)
container_db_failed=$(docker ps -a -f name=${prod_container_db_name} --format "{{.Status}}" | head -1)

if [[ "${container_failed}" != *"Up"* ]]; then
    docker logs ${prod_container_name}
    docker logs ${prod_container_name} --tail 12 &> ${DISCORD_NOTIFICATION_MESSAGE_FILE}
    exit 1
fi

if [[ "${container_db_failed}" != *"Up"* ]]; then
    docker logs ${prod_container_db_name}
    docker logs ${prod_container_name} --tail 12 &> ${DISCORD_NOTIFICATION_MESSAGE_FILE}
    exit 1
fi
