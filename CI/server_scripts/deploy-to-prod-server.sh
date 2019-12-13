#!/bin/bash

set -e -o xtrace
# https://stackoverflow.com/a/5750463/7734535

testContainerName="${COMPOSE_PROJECT_NAME}_wall_e"
testContainerDBName="${COMPOSE_PROJECT_NAME}_wall_e_db"
docker rm -f ${testContainerName} || true
COMPOSE_PROJECT_NAME_lowerCase=$(echo "$COMPOSE_PROJECT_NAME" | awk '{print tolower($0)}')
testImageName_lowerCase=$(echo "$testContainerName" | awk '{print tolower($0)}')
docker image rm -f ${testImageName_lowerCase} || true
docker volume create --name="${COMPOSE_PROJECT_NAME}_logs"
export ORIGIN_IMAGE="sfucsssorg/wall_e"
docker-compose -f CI/server_scripts/docker-compose.yml up -d
sleep 20

containerFailed=$(docker ps -a -f name=${testContainerName} --format "{{.Status}}" | head -1)
containerDBFailed=$(docker ps -a -f name=${testContainerDBName} --format "{{.Status}}" | head -1)

if [[ "${containerFailed}" != *"Up"* ]]; then
    docker logs ${testContainerName}
    exit 1
    # discordOutput=$(docker logs ${testContainerName} | tail -12)
    # output=$(docker logs ${testContainerName})
    # send following to discord
    # description: BRANCH_NAME + '\n' + discordOutput
    # footer: env.GIT_COMMIT
    # link: env.BUILD_URL
    # successful: false
    # title: "Failing build"
    # webhookURL: $WEBHOOKURL
    # error output
fi

if [[ "${containerDBFailed}" != *"Up"* ]]; then
    docker logs ${testContainerDBName}
    exit 1
    # discordOutput=$(docker logs ${testContainerName} | tail -12)
    # output=$(docker logs ${testContainerName})
    # send following to discord
    # description: BRANCH_NAME + '\n' + discordOutput
    # footer: env.GIT_COMMIT
    # link: env.BUILD_URL
    # successful: false
    # title: "Failing build"
    # webhookURL: $WEBHOOKURL
    # error output
fi
