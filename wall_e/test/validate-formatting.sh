#!/bin/bash
set -e -o xtrace

whoami

pyTestContainerName="${COMPOSE_PROJECT_NAME}XXwall_e_pytest"
ls -l
./wall_e/test/lineEndings.sh
docker rm -f ${pyTestContainerName} || true
pyTestContainerNameLowerCase=$(echo "$pyTestContainerName" | awk '{print tolower($0)}')
docker image rm -f ${pyTestContainerNameLowerCase}
cmd="docker build -t ${pyTestContainerNameLowerCase} \
    --build-arg CONTAINER_HOME_DIR=${CONTAINER_HOME_DIR} \
    --build-arg UNIT_TEST_RESULTS=${UNIT_TEST_RESULTS} -f Dockerfile.test ."
echo $cmd
$cmd

mkdir -p ${UNIT_TEST_RESULTS}
cmd="docker run -d \
    --mount \
    type=bind,source="${WORKSPACE}/${UNIT_TEST_RESULTS}",target="${CONTAINER_HOME_DIR}/${UNIT_TEST_RESULTS}" \
    --net=host --name ${pyTestContainerName} ${pyTestContainerNameLowerCase}"
echo $cmd
$cmd
sleep 20
docker inspect ${pyTestContainerName} --format='{{.State.ExitCode}}' | grep  '0'
testContainerFailed=$?
if [ "${testContainerFailed}" -eq "1" ]; then
    discordOutput=$(docker logs ${pyTestContainerName} | tail -12)
    printf $discordOutput > ${RESULT_FILE}
    exit 1
fi
printf "successful" > ${RESULT_FILE}
exit 0
