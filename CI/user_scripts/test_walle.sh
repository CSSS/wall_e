#!/bin/bash


# PURPOSE: to be used by the user when they want to test their code against the linter

docker stop wall_e_py_test || true
docker rm wall_e_py_test || true
docker image rm wall_e_py_test || true
pushd ../
docker build -t wall_e_py_test -f CI/Dockerfile.test --build-arg CONTAINER_HOME_DIR=/usr/src/app --build-arg UNIT_TEST_RESULTS=/usr/src/app/tests --build-arg TEST_RESULT_FILE_NAME=all-unit-tests.xml .
docker run -d --name wall_e_py_test wall_e_py_test

popd

while [ "$(docker inspect -f '{{.State.Running}}' wall_e_py_test)"  = "true" ]
do
	echo "waiting for testing to complete"
	sleep 1
done

docker logs wall_e_py_test

docker rm -f wall_e_py_test || true
docker image rm wall_e_py_test