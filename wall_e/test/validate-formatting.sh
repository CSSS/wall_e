#!/bin/bash
set -e -o xtrace

./wall_e/test/lineEndings.sh


echo ENVIRONMENT=${ENVIRONMENT}
echo COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME}

echo POSTGRES_DB_USER=${POSTGRES_DB_USER}
echo POSTGRES_DB_DBNAME=${POSTGRES_DB_DBNAME}
echo WALL_E_DB_USER=${WALL_E_DB_USER}
echo WALL_E_DB_DBNAME=${WALL_E_DB_DBNAME}

echo CONTAINER_HOME_DIR=${CONTAINER_HOME_DIR}
echo CONTAINER_TEST_DIR=${CONTAINER_TEST_DIR}
echo CONTAINER_SRC_DIR=${CONTAINER_SRC_DIR}

echo LOCALHOST_SRC_DIR=${LOCALHOST_SRC_DIR}
echo LOCALHOST_TEST_DIR=${LOCALHOST_TEST_DIR}
echo DOCKER_TEST_IMAGE=${DOCKER_TEST_IMAGE}
echo DOCKER_TEST_CONTAINER=${DOCKER_TEST_CONTAINER}

docker rm -f ${DOCKER_TEST_IMAGE} || true
pyTestContainerNameLowerCase=$(echo "$DOCKER_TEST_IMAGE" | awk '{print tolower($0)}')
docker image rm -f ${pyTestContainerNameLowerCase}

rm -r ${LOCALHOST_TEST_DIR}
mkdir -p ${LOCALHOST_TEST_DIR}


docker build -t ${pyTestContainerNameLowerCase} \
    -f CI/Dockerfile.test \
    --build-arg CONTAINER_HOME_DIR=${CONTAINER_HOME_DIR} \
    --build-arg UNIT_TEST_RESULTS=${CONTAINER_TEST_DIR}  .

docker run -d \
    -v ${LOCALHOST_SRC_DIR}:${CONTAINER_SRC_DIR} \
    --mount \
    type=bind,source="${LOCALHOST_TEST_DIR}",target="${CONTAINER_TEST_DIR}" \
    --net=host --name ${DOCKER_TEST_CONTAINER} ${pyTestContainerNameLowerCase}
sleep 20

docker inspect ${DOCKER_TEST_IMAGE} --format='{{.State.ExitCode}}' | grep  '0'
testContainerFailed=$?
if [ "${testContainerFailed}" -eq "1" ]; then
    discordOutput=$(docker logs ${DOCKER_TEST_IMAGE} | tail -12)
    printf $discordOutput > ${RESULT_FILE}
    exit 1
fi
printf "successful" > ${RESULT_FILE}
exit 0
