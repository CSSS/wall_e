#!/bin/bash

pyTestContainerName="${COMPOSE_PROJECT_NAME}_wall_e_pytest"
./lineEndings.sh
docker rm -f ${pyTestContainerName}
pyTestContainerNameLowerCase=$(echo "$a" | awk '{print tolower(${pyTestContainerName})}')
docker image rm -f ${pyTestContainerNameLowerCase}
docker build -t ${pyTestContainerNameLowerCase} -f Dockerfile.test .
docker run -d -e --net=host --name ${pyTestContainerName} ${pyTestContainerNameLowerCase}
sleep 20
docker inspect ${pyTestContainerName} --format='{{.State.ExitCode}}' | grep  '0'
testContainerFailed=$?
if [ "${testContainerFailed}" -eq "1" ]; then
    discordOutput=$(docker logs ${pyTestContainerName} | tail -12)
    output=$(docker logs ${pyTestContainerName})
    # send following to discord
    # description: BRANCH_NAME + '\n' + discordOutput
    # footer: env.GIT_COMMIT
    # link: env.BUILD_URL
    # successful: false
    # title: "Failing build"
    # webhookURL: $WEBHOOKURL
    error output
fi
