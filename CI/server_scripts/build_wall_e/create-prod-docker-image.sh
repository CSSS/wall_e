#!/bin/bash


## PURPOSE: intended to be used by jenkins whenever it needs to re-create the base docker image for a master branch

set -e -o xtrace
# https://stackoverflow.com/a/5750463/7734535

if [ -z "${JENKINS_HOME}" ]; then
    echo "JENKINS_HOME is not set"
    exit 1
fi

if [ -z "${BRANCH_NAME}" ]; then
    echo "BRANCH_NAME is not set"
    exit 1
fi

export docker_registry="sfucsssorg"

export wall_e_top_base_image="wall_e"
export wall_e_top_base_image_dockerfile="CI/server_scripts/build_wall_e/Dockerfile.wall_e_base"
export wall_e_top_base_image_requirements_file_locatiom="wall_e/src/requirements.txt"

export wall_e_bottom_base_image="wall_e_python"
export wall_e_bottom_base_image_dockerfile="CI/server_scripts/build_wall_e/Dockerfile.python_base"
export wall_e_bottom_base_image_requirements_file_locatiom="CI/server_scripts/build_wall_e/python-base-requirements.txt"

export commit_folder="wall_e_commits"

export test_container_db_name="TEST_${BRANCH_NAME}_wall_e_db"
export test_container_name="TEST_${BRANCH_NAME}_wall_e"
export test_image_name="test_${branch_name}_wall_e"
export prod_container_name="PRODUCTION_${BRANCH_NAME}_wall_e"
export prod_image_name="production_${branch_name}_wall_e"

export branch_name=$(echo "$BRANCH_NAME" | awk '{print tolower($0)}')


export current_commit=$(git log -1 --pretty=format:"%H")

re_create_bottom_base_image () {
    docker stop "${test_container_db_name}" "${test_container_name}" "${prod_container_name}" || true
    docker rm "${test_container_db_name}" "${test_container_name}" "${prod_container_name}" || true
    docker image rm -f "${prod_image_name}" "${test_image_name}" "${wall_e_bottom_base_image}" \
        "${wall_e_top_base_image}" "${docker_registry}/${wall_e_bottom_base_image}" \
        "${docker_registry}/${wall_e_top_base_image}" || true
    docker build --no-cache -t ${wall_e_bottom_base_image} -f ${wall_e_bottom_base_image_dockerfile} .
    docker tag ${wall_e_bottom_base_image} ${docker_registry}/${wall_e_bottom_base_image}
    echo "${DOCKER_HUB_PASSWORD}" | docker login --username=${DOCKER_HUB_USER_NAME} --password-stdin
    docker push ${docker_registry}/${wall_e_bottom_base_image}
    mkdir -p "${JENKINS_HOME}"/"${commit_folder}"
    echo "${current_commit}" > "${JENKINS_HOME}"/"${commit_folder}"/"${COMPOSE_PROJECT_NAME}_python_base"
    docker image rm "${docker_registry}/${wall_e_bottom_base_image}" "${wall_e_bottom_base_image}"
}

if [ ! -f "${JENKINS_HOME}"/"${commit_folder}"/"${COMPOSE_PROJECT_NAME}_python_base" ]; then
    echo "No previous commits detected. Will [re-]create ${wall_e_bottom_base_image} docker image"
    re_create_bottom_base_image
else
    echo "previous commit detected. Will now test to se if re-creation is needed"
    previous_commit=$(cat "${JENKINS_HOME}"/"${commit_folder}"/"${COMPOSE_PROJECT_NAME}_python_base")
    files_changed=($(git diff --name-only "${current_commit}" "${previous_commit}"))
    for file_changed in "${files_changed[@]}"
    do
        if [[ "${file_changed}" == "${wall_e_bottom_base_image_requirements_file_locatiom}" || "${file_changed}" == "${wall_e_bottom_base_image_dockerfile}" ]]; then
            echo "will need to re-create docker image ${wall_e_bottom_base_image}"
            re_create_bottom_base_image
        fi
    done
fi



re_create_top_base_image () {
    docker stop "${test_container_db_name}" "${test_container_name}" "${prod_container_name}" || true
    docker rm "${test_container_db_name}" "${test_container_name}" "${prod_container_name}" || true
    docker image rm -f "${prod_image_name}" "${test_image_name}" "${wall_e_top_base_image}" \
        "${docker_registry}/${wall_e_top_base_image}" || true
    docker build --no-cache -t ${wall_e_top_base_image} -f ${wall_e_top_base_image_dockerfile} \
        --build-arg CONTAINER_HOME_DIR=${CONTAINER_HOME_DIR} .
    docker tag ${wall_e_top_base_image} ${docker_registry}/${wall_e_top_base_image}
    echo "${DOCKER_HUB_PASSWORD}" | docker login --username=${DOCKER_HUB_USER_NAME} --password-stdin
    docker push ${docker_registry}/${wall_e_top_base_image}
    mkdir -p "${JENKINS_HOME}"/"${commit_folder}"
    echo "${current_commit}" > "${JENKINS_HOME}"/"${commit_folder}"/"${COMPOSE_PROJECT_NAME}_wall_e_base"
    docker image rm "${docker_registry}/${wall_e_top_base_image}" "${wall_e_top_base_image}" "${docker_registry}/${wall_e_bottom_base_image}"
    exit 0
}

if [ ! -f "${JENKINS_HOME}"/"${commit_folder}"/"${COMPOSE_PROJECT_NAME}_wall_e_base" ]; then
    echo "No previous commits detected. Will [re-]create ${wall_e_top_base_image} docker image"
    re_create_top_base_image
else
    echo "previus commit detected. Will now test to se if re-creation is needed"
    previous_commit=$(cat "${JENKINS_HOME}"/"${commit_folder}"/"${COMPOSE_PROJECT_NAME}_wall_e_base")
    files_changed=($(git diff --name-only "${current_commit}" "${previous_commit}"))
    for file_changed in "${files_changed[@]}"
    do
        if [[ "${file_changed}" == "${wall_e_top_base_image_requirements_file_locatiom}" || "${file_changed}" == "${wall_e_top_base_image_dockerfile}" ]]; then
            echo "will need to re-create docker image ${wall_e_top_base_image}"
            re_create_top_base_image
        fi
        if [[ "${file_changed}" == "${wall_e_bottom_base_image_requirements_file_locatiom}" || "${file_changed}" == "${wall_e_bottom_base_image_dockerfile}" ]]; then
            echo "will need to re-create docker image ${wall_e_top_base_image}"
            re_create_top_base_image
        fi
    done
fi

echo "No modifications were needed to the base images"
echo "${current_commit}" > "${JENKINS_HOME}"/"${commit_folder}"/"${COMPOSE_PROJECT_NAME}"
exit 0
