#!/bin/bash

# PURPOSE: used be jenkins to launch Wall_e to the CSSS PROD Discord Guild

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

rm ${DISCORD_NOTIFICATION_MESSAGE_FILE} || true

export compose_project_name=$(echo "$COMPOSE_PROJECT_NAME" | awk '{print tolower($0)}')

export docker_compose_file="CI/validate_and_deploy/2_deploy/server_scripts/docker-compose.yml"

export prod_container_name="${COMPOSE_PROJECT_NAME}_wall_e"
export prod_image_name_lower_case=$(echo "$prod_container_name" | awk '{print tolower($0)}')

export prod_container_db_name="${COMPOSE_PROJECT_NAME}_wall_e_db"

export docker_registry="sfucsssorg"
export wall_e_top_base_image="wall_e_base"
export ORIGIN_IMAGE="${docker_registry}/wall_e"
export WALL_E_PYTHON_BASE_IMAGE="${docker_registry}/wall_e_python"

export wall_e_top_base_image_dockerfile="CI/validate_and_deploy/2_deploy/server_scripts/Dockerfile.wall_e_base"

docker rm -f ${prod_container_name} || true
docker image rm -f ${prod_image_name_lower_case} || true
docker volume create --name="${COMPOSE_PROJECT_NAME}_logs"


re_create_top_base_image () {
    docker image rm -f "${prod_image_name_lower_case}" "${wall_e_top_base_image}" "${ORIGIN_IMAGE}"
    docker system prune -f --all
    docker build --no-cache -t ${wall_e_top_base_image} -f ${wall_e_top_base_image_dockerfile} \
    --build-arg CONTAINER_HOME_DIR=${CONTAINER_HOME_DIR} \
    --build-arg WALL_E_BASE_ORIGIN_NAME=${WALL_E_PYTHON_BASE_IMAGE} .
    docker tag ${wall_e_top_base_image} ${ORIGIN_IMAGE}
    echo "${DOCKER_HUB_PASSWORD}" | docker login --username=${DOCKER_HUB_USER_NAME} --password-stdin
    docker push ${ORIGIN_IMAGE}
    docker image rm -f "${prod_image_name_lower_case}" "${wall_e_top_base_image}" "${ORIGIN_IMAGE}"
    docker system prune -f --all
}

re_create_top_base_image

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
