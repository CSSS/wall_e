#!/bin/bash


export COMPOSE_PROJECT_NAME="TEST_${1}"
./CI/destroy-dev-env.sh
