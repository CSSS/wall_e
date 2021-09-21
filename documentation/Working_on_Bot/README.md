# Working on the Bot

- [Wiki: Creating Bot and Attaching it to a Development Server](https://github.com/CSSS/wall_e/wiki/2.-Creating-Bot-and-Attaching-it-to-a-Development-Server)  
- [Running the Bot](#running-the-bot)  
  - [With dockerized Wall-E](#with-dockerized-wall-e)
    - [view logs in active time](#view-logs-in-active-time)
    - [Re-launching dockerized Wall-E after making changes](#re-launching-dockerized-wall-e-after-making-changes)
  - [Running wall_e outside a docker container [to be able to Debug from Pycharm]](#running-wall_e-outside-a-docker-container-to-be-able-to-debug-from-pycharm)
    - [Re-launching Wall-E after making changes](#re-launching-wall-e-after-making-changes)
- [Testing the bot](#testing-the-bot)
  - [Step 1. Run through the linter](#step-1-run-through-the-linter)
    - [With Docker](#with-docker)
    - [Without Docker](#without-docker)
  - [Step 2. Testing on CSSS Bot Test Server](#step-2-testing-on-csss-bot-test-server)
- [Wiki: Making a PR to master](https://github.com/CSSS/wall_e/wiki/3.-Making-a-PR-to-master)  
- [Test Cases](Test_Cases.md)  
- [Wiki: Reporting Issues](https://github.com/CSSS/wall_e/wiki/4.-Reporting-Issues)  
- [FAQs](#faqs)  


## Running the Bot
>If you encounter any errors doing the following commands, feel free to add it to the [FAQs section](#faqs) for future reference :)

> Due to some compatibility issue that occurs with some of the modules on some OSs, walL_e has been dockerized for both server-side running and local development. In order to work with wall_e, you need only `docker` and `docker-compose` working. If you are using Windows Home or do not want to deal with docker, feel free look to [run wall_e on the localhost](#running-wall_e-outside-a-docker-container-to-be-able-to-debug-from-pycharm)

Pre-requisites: `git`, [`docker`](https://docs.docker.com/install/linux/docker-ce/debian/#set-up-the-repository) and [`docker-compose`](https://docs.docker.com/compose/install/#install-compose)

1. Fork the [Wall-e Repo](https://github.com/CSSS/wall_e.git)  
2. Clone the repo
3. Wall_E Setting Specification.
   1. Wall_e needs parameter specifications. We use the `wall_e/src/resources/utilities/config/local.ini` file to declare any variables and the `CI/user_scripts/wall_e.env` can be optionally used to initialize.
      [Refer to the wiki page on the ini file](https://github.com/CSSS/wall_e/wiki/5.-contents-of-local.ini) for all the settings that wall_e reads from when doing local dev work.
      1. the following values *need* to be saved to the `CI/user_scripts/wall_e.env` file and exported using `../../CI/user_scripts/set_env.sh`:
         1. When running dockerized wall_e:
            1. `COMPOSE_PROJECT_NAME`
            2. `POSTGRES_PASSWORD`
            3. `ORIGIN_IMAGE`
         2. When running wall_e on localhost:
            1. `COMPOSE_PROJECT_NAME`
            2. `POSTGRES_PASSWORD`
            3. `DB_PORT`
            4. `WALL_E_DB_USER`
            5. `WALL_E_DB_PASSWORD`
            6. `WALL_E_DB_DBNAME`
            7. `ENVIRONMENT`
            8. `DOCKERIZED`

*Keep in mind that unless otherwise indicated, all commands have to be run from `/path/to/repo/wall_e/src`*

You will need to recreate the base docker image if you made changes to any of the following files
 * wall_e/src/requirements.txt
 * CI/server_scripts/build_wall_e/Dockerfile.wall_e_base

### With dockerized Wall-E
```shell
echo 'ENVIRONMENT='"'"'LOCALHOST'"'"'' >  ../../CI/user_scripts/wall_e.env
echo 'COMPOSE_PROJECT_NAME='"'"'discord_bot'"'"'' >>  ../../CI/user_scripts/wall_e.env

echo 'POSTGRES_PASSWORD='"'"'postgres_passwd'"'"'' >>  ../../CI/user_scripts/wall_e.env
echo 'DOCKERIZED='"'"'0'"'"'' >>  ../../CI/user_scripts/wall_e.env

echo 'WALL_E_DB_USER='"'"'wall_e'"'"'' >>  ../../CI/user_scripts/wall_e.env
echo 'WALL_E_DB_PASSWORD='"'"'wallEPassword'"'"'' >>  ../../CI/user_scripts/wall_e.env
echo 'WALL_E_DB_DBNAME='"'"'csss_discord_db'"'"'' >>  ../../CI/user_scripts/wall_e.env
echo 'DB_ENABLED='"'"'1'"'"'' >>  ../../CI/user_scripts/wall_e.env

. ../../CI/user_scripts/set_env.sh

echo 'HOST='"'"${COMPOSE_PROJECT_NAME}_wall_e_db"'"'' >> ../../CI/user_scripts/wall_e.env
. ../../CI/user_scripts/set_env.sh

if (you made changes to any of the files listed above){
    ../../CI/user_scripts/create-dev-docker-image.sh
    echo 'ORIGIN_IMAGE='"'"${COMPOSE_PROJECT_NAME}_wall_e_base"'"'' >>  ../../CI/user_scripts/wall_e.env
}else{
    echo 'ORIGIN_IMAGE='"'"'sfucsssorg/wall_e'"'"'' >>  ../../CI/user_scripts/wall_e.env

}
. ../../CI/user_scripts/set_env.sh
 
../../CI/user_scripts/setup-dev-env.sh
````

#### view logs in active time
```shell
 docker logs -f "${COMPOSE_PROJECT_NAME}_wall_e"
```

#### Re-launching dockerized Wall-E after making changes

To re-launch the bot after making some changes, enter the command `.exit` on your discord guild and then run `../../CI/user_scripts/setup-dev-env.sh` again.
You will need to run `../../CI/user_scripts/create-dev-docker-image.sh` again if you made further changes to `wall_e/src/requirements.txt` or `CI/server_scripts/build_wall_e/Dockerfile.wall_e_base`

### Running wall_e outside a docker container [to be able to Debug from Pycharm]
> If launching from inside of PyCharm, I recommend using [EnvFile](https://plugins.jetbrains.com/plugin/7861-envfile) plugin so that the variables in `wall_e.env` get automatically exported by PyCharm
```shell
echo 'ENVIRONMENT='"'"'LOCALHOST'"'"'' >  ../../CI/user_scripts/wall_e.env
echo 'COMPOSE_PROJECT_NAME='"'"'discord_bot'"'"'' >>  ../../CI/user_scripts/wall_e.env
echo 'DOCKERIZED='"'"'0'"'"'' >>  ../../CI/user_scripts/wall_e.env
. ../../CI/user_scripts/set_env.sh

if (you are using a database){
    echo 'POSTGRES_PASSWORD='"'"'postgres_passwd'"'"'' >>  ../../CI/user_scripts/wall_e.env
    echo 'DB_PORT='"'"'5432'"'"'' >>  ../../CI/user_scripts/wall_e.env
    echo 'HOST='"'"'127.0.0.1'"'"'' >>  ../../CI/user_scripts/wall_e.env
    echo 'WALL_E_DB_USER='"'"'wall_e'"'"'' >>  ../../CI/user_scripts/wall_e.env
    echo 'WALL_E_DB_PASSWORD='"'"'wallEPassword'"'"'' >>  ../../CI/user_scripts/wall_e.env
    echo 'WALL_E_DB_DBNAME='"'"'csss_discord_db'"'"'' >>  ../../CI/user_scripts/wall_e.env
    echo 'DB_ENABLED='"'"'1'"'"'' >>  ../../CI/user_scripts/wall_e.env
}else{
    echo 'DB_ENABLED='"'"'0'"'"'' >>  ../../CI/user_scripts/wall_e.env
}
. ../../CI/user_scripts/set_env.sh

python3 -m pip install -r requirements.txt

if (you are using the dockerized database){
  docker run -d --env POSTGRES_PASSWORD=${POSTGRES_PASSWORD} -p "${DB_PORT}":5432 --name "${COMPOSE_PROJECT_NAME}_wall_e_db" postgres:alpine
  PGPASSWORD=$POSTGRES_PASSWORD psql --set=WALL_E_DB_USER="${WALL_E_DB_USER}" \
  --set=WALL_E_DB_PASSWORD="${WALL_E_DB_PASSWORD}"  --set=WALL_E_DB_DBNAME="${WALL_E_DB_DBNAME}" \
  -h "${HOST}" -U "postgres" -f WalleModels/create-database.ddl
  python3 django-db-orm-manage.py makemigrations
  python3 django-db-orm-manage.py migrate
}

python3 main.py
```

#### Re-launching Wall-E after making changes
If you need to re-launch the bot after making some changes, enter the command `.exit` on your discord guild and then run `python3 main.py` again.

## Testing the bot

### Step 1. Run through the [linter](https://en.wikipedia.org/wiki/Lint_%28software%29)

Before you can push your changes to the wall_e repo, you will first need to make sure it passes the unit tests. that can be done like so:

#### With Docker
```shell
./CI/user_scripts/test_walle.sh
```

#### Without Docker
```shell
python3.8 -m virtualenv testENV
. testENV/bin/activate
python3.8 -m pip install -r wall_e/test/test-requirements.txt
cp wall_e/test/pytest.ini wall_e/src/.
cp wall_e/test/validate_line_endings.sh wall_e/src/.
cp wall_e/test/setup.cfg wall_e/src/.
py.test --junitxml=test_results.xml wall_e/src
./wall_e/src/validate-line-endings.sh
```


### Step 2. Testing on [CSSS Bot Test Server](https://discord.gg/85bWteC)
After you have tested on your own Discord Test Server, create a PR to the [Wall-E Repo](https://github.com/CSSS/wall_e/pulls) that follows the [rules](https://github.com/CSSS/wall_e/wiki/3.-Making-a-PR-to-master) for PRs before pushing your changes to Wall-E. Creating the PR will automatically load it into the CSSS Bot Test Server. the name of the channel will be `pr-<PR number>`.  

## FAQs  

### Issue: Experiencing a networking issue with docker-compose

```shell

ERROR: could not find an available, non-overlapping IPv4 address pool among the defaults to assign to the network

```
resolution: If you are using a VPN, please disconnect and try again.
