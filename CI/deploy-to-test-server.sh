#!/bin/bash

set -e

testContainerName="${COMPOSE_PROJECT_NAME}_wall_e"
testContainerDBName="${COMPOSE_PROJECT_NAME}_wall_e_db"
docker rm -f ${testContainerName} ${testContainerDBName}
COMPOSE_PROJECT_NAME_lowerCase=$(echo "$COMPOSE_PROJECT_NAME" | awk '{print tolower($0)}')
testContainerName_lowerCase=$(echo "$testContainerName" | awk '{print tolower($0)}')
docker network rm ${COMPOSE_PROJECT_NAME_lowerCase}_default
docker image rm -f ${testContainerName_lowerCase}
docker volume create --name="${COMPOSE_PROJECT_NAME}_logs"
docker-compose up -d
sleep 20

docker ps -a -f name=${testContainerName} --format "{{.Status}}" | head -1 | grep 'Up'
containerFailed=$?
docker ps -a -f name=${testContainerDBName} --format "{{.Status}}" | head -1 |  grep 'Up'
containerDBFailed=$?
if [ "${containerFailed}" -eq "1" ]; then
    discordOutput=$(docker logs ${testContainerName} | tail -12)
    output=$(docker logs ${testContainerName})
    # send following to discord
    # description: BRANCH_NAME + '\n' + discordOutput
    # footer: env.GIT_COMMIT
    # link: env.BUILD_URL
    # successful: false
    # title: "Failing build"
    # webhookURL: $WEBHOOKURL
    error output
fi

if [ "${containerDBFailed}" -eq "1" ]; then
    discordOutput=$(docker logs ${testContainerName} | tail -12)
    output=$(docker logs ${testContainerName})
    # send following to discord
    # description: BRANCH_NAME + '\n' + discordOutput
    # footer: env.GIT_COMMIT
    # link: env.BUILD_URL
    # successful: false
    # title: "Failing build"
    # webhookURL: $WEBHOOKURL
    error output
fi
