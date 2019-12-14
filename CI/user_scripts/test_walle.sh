#!/bin/bash


docker stop ${COMPOSE_PROJECT_NAME}_test || true
docker rm ${COMPOSE_PROJECT_NAME}_test || true
docker image rm ${COMPOSE_PROJECT_NAME}_wall_e_test || true
docker build -t ${COMPOSE_PROJECT_NAME}_wall_e_test -f CI/Dockerfile.test --build-arg CONTAINER_HOME_DIR=/usr/src/app --build-arg UNIT_TEST_RESULTS=/usr/src/app/tests --build-arg TEST_RESULT_FILE_NAME=all-unit-tests.xml .
docker run -d --name ${COMPOSE_PROJECT_NAME}_test ${COMPOSE_PROJECT_NAME}_wall_e_test
echo "*****************************************************"
echo "**********run docker logs ${COMPOSE_PROJECT_NAME}_test**********"
echo "*****************************************************"
