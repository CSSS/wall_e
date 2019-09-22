#!/bin/bash

set -e

IMAGENAME="wall_e"
DOCKERREGISTRY="sfucsssorg/wall_e"
VERSION="0.0.1"
DOCKERFILE="Dockerfile.walle.base"


past_2_commits=($(git log -2 --pretty=format:"%h"))
files_changed=($(git diff --name-only $(echo ${past_2_commits[*]})))

for file_changed in "${files_changed[@]}"
do
    if [ "${file_changed}" == "requirements.txt" ]; then
        docker image rm -f wall_e || true
        cmd="docker build -t ${IMAGENAME} \
            --build-arg CONTAINER_HOME_DIR=${CONTAINER_HOME_DIR} \
            --build-arg UNIT_TEST_RESULTS=${UNIT_TEST_RESULTS} -f ${DOCKERFILE}. ."
        echo $cmd
        $cmd
        docker tag ${IMAGENAME} ${DOCKERREGISTRY}/${IMAGENAME}
        docker tag ${IMAGENAME} ${DOCKERREGISTRY}/${IMAGENAME}:${VERSION}
        docker push ${DOCKERREGISTRY}/${IMAGENAME}
        docker push ${DOCKERREGISTRY}/${IMAGENAME}:${VERSION}
        exit 0
    fi
done
