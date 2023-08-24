#!/bin/bash


## PURPOSE: intended to be used by jenkins whenever it needs to re-create the base docker image for a master branch

set -e -o xtrace
# https://stackoverflow.com/a/5750463/7734535

if [ -z "${JENKINS_HOME}" ]; then
    echo "JENKINS_HOME is not set"
    exit 1
fi

if [ -z "${DOCKER_HUB_PASSWORD}" ]; then
    echo "DOCKER_HUB_PASSWORD is not set"
    exit 1
fi


if [ -z "${DOCKER_HUB_USER_NAME}" ]; then
    echo "DOCKER_HUB_USER_NAME is not set"
    exit 1
fi

#if [ -z "${BRANCH_NAME}" ]; then
#    echo "BRANCH_NAME is not set"
#    exit 1
#fi
#
#export branch_name=$(echo "$BRANCH_NAME" | awk '{print tolower($0)}')


export docker_registry="sfucsssorg"
export wall_e_top_base_image="wall_e_base"
export WALL_E_PYTHON_BASE_IMAGE="${docker_registry}/wall_e_python"
export WALL_E_BASE_IMAGE="${docker_registry}/wall_e"

export wall_e_top_base_image_dockerfile="CI/server_scripts/build_wall_e/Dockerfile.wall_e_base"
export wall_e_top_base_image_requirements_file_location="wall_e/src/requirements.txt"

export commit_folder="wall_e_commits"
export WALL_E_BASE_COMMIT_FILE="${JENKINS_HOME}/${commit_folder}/${COMPOSE_PROJECT_NAME}_wall_e_base"

export test_container_db_name="${COMPOSE_PROJECT_NAME}_wall_e_db"
export test_container_name="${COMPOSE_PROJECT_NAME}_wall_e"
export test_image_name=$(echo "${COMPOSE_PROJECT_NAME}_wall_e" | awk '{print tolower($0)}')

export current_commit=$(git log -1 --pretty=format:"%H")


re_create_top_base_image () {
    docker stop "${test_container_db_name}" "${test_container_name}" || true
    docker rm "${test_container_db_name}" "${test_container_name}" || true
    docker image rm -f "${test_image_name}" "${wall_e_top_base_image}" "${WALL_E_BASE_IMAGE}" || true
    docker build --no-cache -t ${wall_e_top_base_image} -f ${wall_e_top_base_image_dockerfile} --build-arg CONTAINER_HOME_DIR=${CONTAINER_HOME_DIR} --build-arg WALL_E_BASE_ORIGIN_NAME=${WALL_E_PYTHON_BASE_IMAGE} .
    docker tag ${wall_e_top_base_image} ${WALL_E_BASE_IMAGE}
    echo "${DOCKER_HUB_PASSWORD}" | docker login --username=${DOCKER_HUB_USER_NAME} --password-stdin
    docker push ${WALL_E_BASE_IMAGE}
    mkdir -p "${JENKINS_HOME}"/"${commit_folder}"
    docker image rm "${WALL_E_PYTHON_BASE_IMAGE}" "${wall_e_top_base_image}" "${WALL_E_BASE_IMAGE}"
    exit 0
}

if [ ! -f "${WALL_E_BASE_COMMIT_FILE}" ]; then
    echo "No previous commits detected. Will [re-]create ${wall_e_top_base_image} docker image"
    re_create_top_base_image
else
    echo "previus commit detected. Will now test to se if re-creation is needed"
    previous_commit=$(cat "${WALL_E_BASE_COMMIT_FILE}")
    files_changed=($(git diff --name-only "${current_commit}" "${previous_commit}"))
    for file_changed in "${files_changed[@]}"
    do
        if [[ "${file_changed}" == "${wall_e_top_base_image_requirements_file_location}" || "${file_changed}" == "${wall_e_top_base_image_dockerfile}" ]]; then
            echo "will need to re-create docker image ${wall_e_top_base_image}"
            re_create_top_base_image
        fi
    done
fi

echo "${current_commit}" > "${WALL_E_BASE_COMMIT_FILE}"

echo "No modifications were needed to the base images"
exit 0
