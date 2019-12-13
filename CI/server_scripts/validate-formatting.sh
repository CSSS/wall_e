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
DOCKER_TEST_IMAGE=$(echo "$DOCKER_TEST_IMAGE" | awk '{print tolower($0)}')

docker rm -f ${DOCKER_TEST_CONTAINER} || true
docker image rm -f ${DOCKER_TEST_IMAGE} || true

rm -r ${LOCALHOST_TEST_DIR} || true
mkdir -p ${LOCALHOST_TEST_DIR}


docker build --no-cache -t ${DOCKER_TEST_IMAGE} \
    -f CI/Dockerfile.test \
    --build-arg CONTAINER_HOME_DIR=${CONTAINER_HOME_DIR} \
    --build-arg UNIT_TEST_RESULTS=${CONTAINER_TEST_DIR} \
    --build-arg TEST_RESULT_FILE_NAME=${TEST_RESULT_FILE_NAME} .

docker run -d --name ${DOCKER_TEST_CONTAINER} ${DOCKER_TEST_IMAGE}
sleep 20
sudo docker cp ${DOCKER_TEST_CONTAINER}:${CONTAINER_TEST_DIR}/${TEST_RESULT_FILE_NAME} ${LOCALHOST_TEST_DIR}/${TEST_RESULT_FILE_NAME}

testContainerFailed=$(docker inspect ${DOCKER_TEST_CONTAINER} --format='{{.State.ExitCode}}')

if [ "${testContainerFailed}" -eq "1" ]; then
    docker logs ${DOCKER_TEST_CONTAINER}
    docker stop ${DOCKER_TEST_CONTAINER} || true
    docker rm ${DOCKER_TEST_CONTAINER} || true
    docker image rm -f ${DOCKER_TEST_IMAGE} || true
    exit 1
fi

docker stop ${DOCKER_TEST_CONTAINER} || true
docker rm ${DOCKER_TEST_CONTAINER} || true
docker image rm -f ${DOCKER_TEST_IMAGE} || true
exit 0
