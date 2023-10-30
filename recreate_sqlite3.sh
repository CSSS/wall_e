#!/bin/bash
. ./CI/user_scripts/set_env.sh
pushd wall_e
rm ../db.sqlite3 || true
python3 django_manage.py migrate
rm wall_e.json* || true
wget https://dev.sfucsss.org/wall_e/fixtures/wall_e.json
python3 django_manage.py loaddata wall_e.json
rm wall_e.json* || true
popd