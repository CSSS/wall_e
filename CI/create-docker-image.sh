#!/bin/bash

set -e -o xtrace
# https://stackoverflow.com/a/5750463/7734535

IMAGENAME="wall_e"
DOCKERREGISTRY="sfucsssorg"
VERSION="0.0.1"
DOCKERFILE="CI/Dockerfile.requirements"


past_2_commits=($(git log -2 --pretty=format:"%h"))
files_changed=($(git diff --name-only $(echo ${past_2_commits[*]})))

for file_changed in "${files_changed[@]}"
do
    if [ "${file_changed}" == "wall_e/src/requirements.txt" ]; then
        echo "${DOCKER_HUB_PASSWORD}" | docker login --username=${DOCKER_HUB_USER_NAME} --password-stdin
        docker image rm -f wall_e || true
        docker build -t ${IMAGENAME} \
            --build-arg CONTAINER_HOME_DIR=${CONTAINER_HOME_DIR} \
            -f ${DOCKERFILE} .
        docker tag ${IMAGENAME} ${DOCKERREGISTRY}/${IMAGENAME}
        docker tag ${IMAGENAME} ${DOCKERREGISTRY}/${IMAGENAME}:${VERSION}
        docker push ${DOCKERREGISTRY}/${IMAGENAME}
        docker push ${DOCKERREGISTRY}/${IMAGENAME}:${VERSION}
        exit 0
    fi
done
