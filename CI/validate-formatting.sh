#!/bin/bash

pyTestContainerName="${COMPOSE_PROJECT_NAME}_wall_e_pytest"
./lineEndings.sh
docker rm -f ${pyTestContainerName}
pyTestContainerNameLowerCase=$(echo "$pyTestContainerName" | awk '{print tolower($0)}')
docker image rm -f ${pyTestContainerNameLowerCase}
cmd="docker build -t ${pyTestContainerNameLowerCase} \
    --build-arg DOCKER_CONTAINER_TEST_RESULT_DIRECTORY=${DOCKER_CONTAINER_TEST_RESULT_DIRECTORY} \
    UNIT_TEST_RESULTS=${UNIT_TEST_RESULTS} -f Dockerfile.test ."
echo $cmd
$cmd

mkdir -p ${UNIT_TEST_RESULTS}
docker run -d \
    --mount type=bind,source="${WORKSPACE}/${UNIT_TEST_RESULTS}",target="${DOCKER_CONTAINER_TEST_RESULT_DIRECTORY}/${UNIT_TEST_RESULTS}" \
    --net=host --name ${pyTestContainerName} ${pyTestContainerNameLowerCase}

sleep 20
docker inspect ${pyTestContainerName} --format='{{.State.ExitCode}}' | grep  '0'
testContainerFailed=$?
if [ "${testContainerFailed}" -eq "1" ]; then
    discordOutput=$(docker logs ${pyTestContainerName} | tail -12)
    output=$(docker logs ${pyTestContainerName})
    printf $discordOutput > wall_e_file
    echo -e $output
    exit 1
fi
printf "successful" > wall_e_file
exit 0
