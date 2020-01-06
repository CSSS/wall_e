#!/bin/bash


## PURPOSE: intended to be used by jenkins whenever it needs to re-create the base docker image for a master branch

set -e -o xtrace
# https://stackoverflow.com/a/5750463/7734535

export image_name="wall_e"
export docker_registry="sfucsssorg"
export dockerfile="CI/server_scripts/Dockerfile.base"
export commit_folder="wall_e_commits"

export test_container_db_name="TEST_${BRANCH_NAME}_wall_e_db"
export test_container_name="TEST_${BRANCH_NAME}_wall_e"
export prod_container_name="PRODUCTION_${BRANCH_NAME}_wall_e"

export branch_name=$(echo "$BRANCH_NAME" | awk '{print tolower($0)}')

export prod_image_name="production_${branch_name}_wall_e"
export test_image_name="test_${branch_name}_wall_e"
export requirements_file_locatiom="wall_e/src/requirements.txt"

export current_commit=$(git log -1 --pretty=format:"%H")

re_create_image () {
    docker stop "${test_container_db_name}" "${test_container_name}" "${prod_container_name}" || true
    docker rm "${test_container_db_name}" "${test_container_name}" "${prod_container_name}" || true
    docker image rm -f "${prod_image_name}" "${test_image_name}" "${image_name}" "${docker_registry}/${image_name}" || true
    docker build --no-cache -t ${image_name} -f ${dockerfile} --build-arg CONTAINER_HOME_DIR=${CONTAINER_HOME_DIR} .
    docker tag ${image_name} ${docker_registry}/${image_name}
    echo "${DOCKER_HUB_PASSWORD}" | docker login --username=${DOCKER_HUB_USER_NAME} --password-stdin
    docker push ${docker_registry}/${image_name}
    mkdir -p "${JENKINS_HOME}"/"${commit_folder}"
    echo "${current_commit}" > "${JENKINS_HOME}"/"${commit_folder}"/"${COMPOSE_PROJECT_NAME}"
    exit 0
}

if [ ! -f "${JENKINS_HOME}"/"${commit_folder}"/"${COMPOSE_PROJECT_NAME}" ]; then
    echo "No previous commits detected. Will [re-]create ${testBaseImageName_lowerCase} docker image"
    re_create_image
else
    echo "previus commit detected. Will now test to se if re-creation is needed"
    previous_commit=$(cat "${JENKINS_HOME}"/"${commit_folder}"/"${COMPOSE_PROJECT_NAME}")
    files_changed=($(git diff --name-only "${current_commit}" "${previous_commit}"))
    for file_changed in "${files_changed[@]}"
    do
        if [[ "${file_changed}" == "${requirements_file_locatiom}" || "${file_changed}" == "${dockerfile}" ]]; then
            echo "will need to re-create docker image ${testBaseImageName_lowerCase}"
            re_create_image
        fi
    done
fi

echo "No modifications were needed to base image"
echo "${current_commit}" > "${JENKINS_HOME}"/"${commit_folder}"/"${COMPOSE_PROJECT_NAME}"
exit 0
