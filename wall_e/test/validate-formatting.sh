#!/bin/bash
set -e -o xtrace

whoami

export CONTAINER_TEST_DIR=${CONTAINER_HOME_DIR}/tests
export CONTAINER_SRC_DIR=${CONTAINER_HOME_DIR}/src

export CONTAINER_TEST_DIR=${CONTAINER_HOME_DIR}/tests
export CONTAINER_SRC_DIR=${CONTAINER_HOME_DIR}/src

export DOCKER_TEST_IMAGE=${COMPOSE_PROJECT_NAME}_wall_e_pytest
export DOCKER_TEST_CONTAINER=${COMPOSE_PROJECT_NAME}_pytest

echo LOCALHOST_TEST_DIR=${LOCALHOST_TEST_DIR}

./wall_e/test/lineEndings.sh

pyTestContainerName="${DOCKER_TEST_IMAGE}"
docker rm -f ${pyTestContainerName} || true
pyTestContainerNameLowerCase=$(echo "$pyTestContainerName" | awk '{print tolower($0)}')
docker image rm -f ${pyTestContainerNameLowerCase}
mkdir -p ${UNIT_TEST_RESULTS}


docker build -t ${pyTestContainerNameLowerCase} \
    -f CI/Dockerfile.test \
    --build-arg CONTAINER_HOME_DIR=${CONTAINER_HOME_DIR} \
    --build-arg UNIT_TEST_RESULTS=${CONTAINER_TEST_DIR}  .

docker run -d \
    -v ${LOCALHOST_SRC_DIR}:{CONTAINER_SRC_DIR} \
    --mount \
    type=bind,source="${LOCALHOST_TEST_DIR}",target="${CONTAINER_TEST_DIR}" \
    --net=host --name ${DOCKER_TEST_CONTAINER} ${pyTestContainerNameLowerCase}
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
