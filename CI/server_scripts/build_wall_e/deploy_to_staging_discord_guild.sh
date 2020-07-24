#!/bin/bash

# PURPOSE: used be jenkins to launch Wall_e to the CSSS Staging Discord Guild

set -e -o xtrace
# https://stackoverflow.com/a/5750463/7734535

# required if the docker image needs to be created and cannot just use sfucsssorg/wall_e
if [ -z "${JENKINS_HOME}" ]; then
    echo "JENKINS_HOME is not set"
    exit 1
fi
if [ -z "${BRANCH_NAME}" ]; then
    echo "BRANCH_NAME is not set"
    exit 1
fi

rm ${DISCORD_NOTIFICATION_MESSAGE_FILE} || true

# the variables required to check if the wall_e staging version successfully deployed to the staging discord guild
export test_container_db_name="${COMPOSE_PROJECT_NAME}_wall_e_db"
export test_container_name="${COMPOSE_PROJECT_NAME}_wall_e"
export test_image_name_lower_case=$(echo "$test_container_name" | awk '{print tolower($0)}')
export compose_project_name_lower_case=$(echo "$COMPOSE_PROJECT_NAME" | awk '{print tolower($0)}')
export docker_compose_file="CI/server_scripts/build_wall_e/docker-compose.yml"

# the variables required if either of the wall-e docker images need to be re-created
export commit_folder="wall_e_commits"
export GIT_LATEST_MASTER_COMMIT_FILE="${JENKINS_HOME}/${commit_folder}/TEST_master"
export test_image_name=$(echo "${COMPOSE_PROJECT_NAME}_wall_e" | awk '{print tolower($0)}')
export branch_name=$(echo "$BRANCH_NAME" | awk '{print tolower($0)}')
export current_commit=$(git log -1 --pretty=format:"%H")
export wall_e_top_base_image=$(echo "${COMPOSE_PROJECT_NAME}_wall_e_base_image" | awk '{print tolower($0)}')
export wall_e_bottom_base_image_dockerfile="CI/server_scripts/build_wall_e/Dockerfile.python_base"
export wall_e_bottom_base_image_requirements_file_locatiom="CI/server_scripts/build_wall_e/python-base-requirements.txt"

# the variables required if only the wall_e base docker images need to be re-created
export wall_e_top_base_image_dockerfile="CI/server_scripts/build_wall_e/Dockerfile.wall_e_base"
export wall_e_top_base_image_requirements_file_locatiom="wall_e/src/requirements.txt"

# the variables required if only the python base docker images need to be re-created
export wall_e_bottom_base_image=$(echo "${COMPOSE_PROJECT_NAME}_wall_e_python_base_image" | awk '{print tolower($0)}')

./CI/destroy-dev-env.sh

# handles creating the python_base image
# will result in the origin name for the wall_e base image to be set to either "sfucsssorg/wall_e_python" [if no change is needed] or $wall_e_bottom_base_image [if the image had to be built]
export WALL_E_BASE_ORIGIN_NAME="sfucsssorg/wall_e_python"
re_create_bottom_base_image () {
    docker stop "${test_container_db_name}" "${test_container_name}" || true
    docker rm "${test_container_db_name}" "${test_container_name}"|| true
    docker image rm -f "${test_image_name}" "${wall_e_bottom_base_image}" "${wall_e_top_base_image}" || true
    docker build --no-cache -t ${wall_e_bottom_base_image} -f ${wall_e_bottom_base_image_dockerfile} .
    mkdir -p "${JENKINS_HOME}"/"${commit_folder}"
    echo "${current_commit}" > "${JENKINS_HOME}"/"${commit_folder}"/"${COMPOSE_PROJECT_NAME}_python_base"
    export WALL_E_BASE_ORIGIN_NAME="${wall_e_bottom_base_image}"
}
if [ ! -f "${JENKINS_HOME}"/"${commit_folder}"/"${COMPOSE_PROJECT_NAME}_python_base" ]; then
    echo "No previous commits detected. Will revert to the git commit from master"
    export previous_commit=$(cat ${GIT_LATEST_MASTER_COMMIT_FILE})
else
    echo "previous commit detected. Will now test to se if re-creation is needed"
    export previous_commit=$(cat "${JENKINS_HOME}"/"${commit_folder}"/"${COMPOSE_PROJECT_NAME}_python_base")

fi
files_changed=($(git diff --name-only "${current_commit}" "${previous_commit}"))
for file_changed in "${files_changed[@]}"
do
    if [[ "${file_changed}" == "${wall_e_bottom_base_image_requirements_file_locatiom}" || "${file_changed}" == "${wall_e_bottom_base_image_dockerfile}" ]]; then
        echo "will need to re-create docker image ${wall_e_bottom_base_image}"
        re_create_bottom_base_image
        break
    fi
done

# handles creating the waLl_e base image
# will result in the origin name for the wall_e image to be set to either "sfucsssorg/wall_e" [if no change is needed] or $wall_e_top_base_image [if the image had to be built]
export ORIGIN_IMAGE="sfucsssorg/wall_e"
re_create_top_base_image () {
    docker stop "${test_container_db_name}" "${test_container_name}" || true
    docker rm "${test_container_db_name}" "${test_container_name}"|| true
    docker image rm -f "${test_image_name}" "${wall_e_top_base_image}" || true
    docker build --no-cache -t ${wall_e_top_base_image} -f ${wall_e_top_base_image_dockerfile} \
        --build-arg CONTAINER_HOME_DIR=${CONTAINER_HOME_DIR} --build-arg WALL_E_BASE_ORIGIN_NAME=${WALL_E_BASE_ORIGIN_NAME} .
    mkdir -p "${JENKINS_HOME}"/"${commit_folder}"
    echo "${current_commit}" > "${JENKINS_HOME}"/"${commit_folder}"/"${COMPOSE_PROJECT_NAME}_wall_e_base"
    export ORIGIN_IMAGE="${wall_e_top_base_image}"
  }

if [ ! -f "${JENKINS_HOME}"/"${commit_folder}"/"${COMPOSE_PROJECT_NAME}_wall_e_base" ]; then
    echo "No previous commits detected. Will revert to the git commit from master"
    export previous_commit=$(cat ${GIT_LATEST_MASTER_COMMIT_FILE})

else
    echo "previous commit detected. Will now test to se if re-creation is needed"
    previous_commit=$(cat "${JENKINS_HOME}"/"${commit_folder}"/"${COMPOSE_PROJECT_NAME}_wall_e_base")
fi
files_changed=($(git diff --name-only "${current_commit}" "${previous_commit}"))
for file_changed in "${files_changed[@]}"
do
    if [[ "${file_changed}" == "${wall_e_top_base_image_requirements_file_locatiom}" || "${file_changed}" == "${wall_e_top_base_image_dockerfile}" ]]; then
        echo "will need to re-create docker image ${wall_e_top_base_image}"
        re_create_top_base_image
        break
    elif [[ "${file_changed}" == "${wall_e_bottom_base_image_requirements_file_locatiom}" || "${file_changed}" == "${wall_e_bottom_base_image_dockerfile}" ]]; then
        echo "will need to re-create docker image ${wall_e_top_base_image}"
        re_create_top_base_image
        break
    fi
done


docker volume create --name="${COMPOSE_PROJECT_NAME}_logs"

echo "ORIGIN_IMAGE=${ORIGIN_IMAGE}"
docker-compose -f "${docker_compose_file}" up --force-recreate  -d
sleep 20

export container_failed=$(docker ps -a -f name=${test_container_name} --format "{{.Status}}" | head -1)
export container_db_failed=$(docker ps -a -f name=${test_container_db_name} --format "{{.Status}}" | head -1)
if [[ "${container_failed}" != *"Up"* ]]; then
    docker logs ${test_container_name}
    docker logs ${test_container_name} --tail 12 &> ${DISCORD_NOTIFICATION_MESSAGE_FILE}
    exit 1
fi

if [[ "${container_db_failed}" != *"Up"* ]]; then
    docker logs ${test_container_db_name}
    docker logs ${test_container_db_name} --tail 12 &> ${DISCORD_NOTIFICATION_MESSAGE_FILE}
    exit 1
fi
