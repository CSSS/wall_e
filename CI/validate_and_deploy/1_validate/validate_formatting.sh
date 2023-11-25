#!/bin/bash

# PURPOSE: used by jenkins to run the code past the linter

set -e -o xtrace

rm ${DISCORD_NOTIFICATION_MESSAGE_FILE} || true

docker_test_image_lower_case=$(echo "$DOCKER_TEST_IMAGE" | awk '{print tolower($0)}')

docker rm -f ${DOCKER_TEST_CONTAINER} || true
docker image rm -f ${docker_test_image_lower_case} || true

rm -r ${LOCALHOST_TEST_DIR} || true
mkdir -p ${LOCALHOST_TEST_DIR}


docker build --no-cache -t ${docker_test_image_lower_case} \
    -f CI/validate_and_deploy/1_validate/Dockerfile.test \
    --build-arg CONTAINER_HOME_DIR=${CONTAINER_HOME_DIR} \
    --build-arg UNIT_TEST_RESULTS=${CONTAINER_TEST_DIR} \
    --build-arg TEST_RESULT_FILE_NAME=${TEST_RESULT_FILE_NAME} .

docker run -d --name ${DOCKER_TEST_CONTAINER} ${docker_test_image_lower_case}
while [ "$(docker inspect -f '{{.State.Running}}' ${DOCKER_TEST_CONTAINER})" == "true" ]
do
	echo "waiting for the python formatting validation to finish"
	sleep 1
done
sudo docker cp ${DOCKER_TEST_CONTAINER}:${CONTAINER_TEST_DIR}/${TEST_RESULT_FILE_NAME} ${LOCALHOST_TEST_DIR}/${TEST_RESULT_FILE_NAME}

test_container_failed=$(docker inspect ${DOCKER_TEST_CONTAINER} --format='{{.State.ExitCode}}')

if [ "${test_container_failed}" -eq "1" ]; then
    docker logs ${DOCKER_TEST_CONTAINER}
    docker logs ${DOCKER_TEST_CONTAINER} --tail 12 &> ${DISCORD_NOTIFICATION_MESSAGE_FILE}
    docker stop ${DOCKER_TEST_CONTAINER} || true
    docker rm ${DOCKER_TEST_CONTAINER} || true
    docker image rm -f ${docker_test_image_lower_case} || true
    exit 1
fi

docker stop ${DOCKER_TEST_CONTAINER} || true
docker rm ${DOCKER_TEST_CONTAINER} || true
docker image rm -f ${docker_test_image_lower_case} || true
exit 0
