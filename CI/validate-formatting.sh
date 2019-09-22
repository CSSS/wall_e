#!/bin/bash

set -e

pyTestContainerName="${COMPOSE_PROJECT_NAME}_wall_e_pytest"
./lineEndings.sh
docker rm -f ${pyTestContainerName} || true
pyTestContainerNameLowerCase=$(echo "$pyTestContainerName" | awk '{print tolower($0)}')
docker image rm -f ${pyTestContainerNameLowerCase}
cmd="docker build -t ${pyTestContainerNameLowerCase} \
    --build-arg CONTAINER_HOME_DIR=${CONTAINER_HOME_DIR} \
    --build-arg UNIT_TEST_RESULTS=${UNIT_TEST_RESULTS} -f Dockerfile.test ."
echo $cmd
$cmd

echo "first step"
mkdir -p ${UNIT_TEST_RESULTS}
echo "second step"
cmd="docker run -d \
    --mount \
    type=bind,source="${WORKSPACE}/${UNIT_TEST_RESULTS}",target="${CONTAINER_HOME_DIR}/${UNIT_TEST_RESULTS}" \
    --net=host --name ${pyTestContainerName} ${pyTestContainerNameLowerCase}"
echo $cmd
$cmd
echo "third step"
sleep 20
echo "fourth step"
docker inspect ${pyTestContainerName} --format='{{.State.ExitCode}}' | grep  '0'
testContainerFailed=$?
echo "fifth step"
if [ "${testContainerFailed}" -eq "1" ]; then
    echo "sixth step"
    discordOutput=$(docker logs ${pyTestContainerName} | tail -12)
    echo "seventh step"
    output=$(docker logs ${pyTestContainerName})
    echo "eighth step"
    printf $discordOutput > wall_e_file
    echo "ninth step"
    echo -e $output
    echo "tenth step"
    exit 1
fi
echo "eleventh step"
printf "successful" > wall_e_file
exit 0
