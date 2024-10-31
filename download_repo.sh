#!/bin/bash

set -e

echo "Please enter the HTTPS clone URL for your forked repo"
read forked_repo_https_clone_url
while [ "${forked_repo_https_clone_url}" == "https://github.com/CSSS/wall_e.git" ];
do
  echo "This is not a forked REPO url...Please enter the HTTPS clone URL for your forked repo"
  read forked_repo_https_clone_url
done

git clone --recurse-submodules "${forked_repo_https_clone_url}"
cd wall_e/
./run_walle.sh
