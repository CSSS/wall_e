#!/bin/bash

pyTestContainerName="${COMPOSE_PROJECT_NAME}_wall_e_pytest"
./lineEndings.sh
docker rm -f ${pyTestContainerName}
pyTestContainerNameLowerCase=$(echo "$pyTestContainerName" | awk '{print tolower($0)}')
docker image rm -f ${pyTestContainerNameLowerCase}
docker build -t ${pyTestContainerNameLowerCase} \
    --build-arg UNIT_TEST_RESULTS=mount/unit_results.xml  -f Dockerfile.test .
mkdir -p ${UNIT_TEST_RESULTS}
docker run -d --mount type=bind,source="${UNIT_TEST_RESULTS}",target=${UNIT_TEST_RESULTS} \
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
