#!/bin/bash
set -e -o xtrace

whoami

pyTestContainerName="${DOCKER_TEST_IMAGE}"
ls -l
./wall_e/test/lineEndings.sh
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
