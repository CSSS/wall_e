#!/bin/bash

pyTestContainerName="${COMPOSE_PROJECT_NAME}_wall_e_pytest"
./lineEndings.sh
docker rm -f ${pyTestContainerName}
pyTestContainerNameLowerCase=$(echo "$pyTestContainerName" | awk '{print tolower($0)}')
docker image rm -f ${pyTestContainerNameLowerCase}
docker build -t ${pyTestContainerNameLowerCase} -f Dockerfile.test .
docker run -d -e --net=host --name ${pyTestContainerName} ${pyTestContainerNameLowerCase}
sleep 20
docker inspect ${pyTestContainerName} --format='{{.State.ExitCode}}' | grep  '0'
testContainerFailed=$?
if [ "${testContainerFailed}" -eq "1" ]; then
    discordOutput=$(docker logs ${pyTestContainerName} | tail -12)
    output=$(docker logs ${pyTestContainerName})
    printf $discordOutput > wall_e_file
    echo $output
    exit 1
fi
printf "successful" > wall_e_file
exit 0
