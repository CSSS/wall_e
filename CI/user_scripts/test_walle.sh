#!/bin/bash


# PURPOSE: to be used by the user when they want to test their code against the linter

if [ -z "${COMPOSE_PROJECT_NAME}" ]; then
	echo "COMPOSE_PROJECT_NAME is not set, exiting."
	exit 1
fi
prev_compose_project_name="${COMPOSE_PROJECT_NAME}"
COMPOSE_PROJECT_NAME="tester"

docker stop ${COMPOSE_PROJECT_NAME}_test || true
docker rm ${COMPOSE_PROJECT_NAME}_test || true
docker image rm ${COMPOSE_PROJECT_NAME}_wall_e_test || true
pushd ../../
docker build -t ${COMPOSE_PROJECT_NAME}_wall_e_test -f CI/Dockerfile.test --build-arg CONTAINER_HOME_DIR=/usr/src/app --build-arg UNIT_TEST_RESULTS=/usr/src/app/tests --build-arg TEST_RESULT_FILE_NAME=all-unit-tests.xml .
docker run -d --name ${COMPOSE_PROJECT_NAME}_test ${COMPOSE_PROJECT_NAME}_wall_e_test

popd

while [ "$(docker inspect -f '{{.State.Running}}' ${COMPOSE_PROJECT_NAME}_test)"  = "true" ]
do
	echo "waiting for testing to complete"
	sleep 1
done

docker logs ${COMPOSE_PROJECT_NAME}_test
COMPOSE_PROJECT_NAME="${prev_compose_project_name}"
