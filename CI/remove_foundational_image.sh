#!/bin/bash

set -e -o xtrace
# https://stackoverflow.com/a/5750463/7734535

branch_name="${1}"
export COMPOSE_PROJECT_NAME="TEST_${1}"

export wall_e_top_base_image=$(echo "${COMPOSE_PROJECT_NAME}_wall_e_base_image" | awk '{print tolower($0)}')
export test_image_name=$(echo "${COMPOSE_PROJECT_NAME}_wall_e" | awk '{print tolower($0)}')
export wall_e_bottom_base_image=$(echo "${COMPOSE_PROJECT_NAME}_wall_e_python_base_image" | awk '{print tolower($0)}')
docker image rm "${wall_e_top_base_image}" || true
docker image rm "${test_image_name}" || true
docker image rm "${wall_e_bottom_base_image}" || true
if [ ! -z "${JENKINS_HOME}" ]; then
    export commit_folder="wall_e_commits"
    export WALL_E_PYTHON_BASE_COMMIT_FILE="${JENKINS_HOME}/${commit_folder}/${COMPOSE_PROJECT_NAME}_python_base"
    export WALL_E_BASE_COMMIT_FILE="${JENKINS_HOME}/${commit_folder}/${COMPOSE_PROJECT_NAME}_wall_e_base"
    rm "${WALL_E_PYTHON_BASE_COMMIT_FILE}" || true
    rm "${WALL_E_BASE_COMMIT_FILE}" || true
fi
