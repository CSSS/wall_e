# Working on the Bot

- [Wiki: Creating Bot and Attaching it to a Development Server](https://github.com/CSSS/wall_e/wiki/2.-Creating-Bot-and-Attaching-it-to-a-Development-Server)  
- [Running the Bot](#running-the-bot)  
  - [With the Database](#with-the-database)
    - [With docker-ized Wall-E](#with-docker-ized-wall-e)
    - [Running wall_e outside of a docker container [to be able to Debug from Pycharm]](#running-wall_e-outside-of-a-docker-container-[to-be-able-to-Debug-from-Pycharm])
  - [Without the Database](#without-the-database)
- [Testing the Bot](#testing-the-bot)
  - [Step 1. Run through the linter](#step-1-run-through-the-linter)
  - [Step 2. Testing on the CSSS Bot Test Server](#step-2-testing-on-csss-bot-test-server)
- [Wiki: Making a PR to master](https://github.com/CSSS/wall_e/wiki/3.-Making-a-PR-to-master)  
- [Test Cases](Test_Cases.md)  
- [Wiki: Reporting Issues](https://github.com/CSSS/wall_e/wiki/4.-Reporting-Issues)  
- [FAQs](#faqs)  


## Running the Bot
>If you encounter any errors doing the following commands, feel free to add it to the [FAQs section](#faqs) for future reference :)

> Due to some compatibility issue that occurs with some of the modules on some OSs, walL_e has been dockerized for both server-side running and local development. In order to work with wall_e, you need only `docker` and `docker-compose` working. If you are using Windows Home or do not want to deal with docker, feel free to use the [Docker-less README](Docker-less/README.md). However, docker-less wall_e does not support any commands that use the database and we will not provide assistance for OS issues that arise from incompabilities with any part of wall_e

Pre-requisites: `git`, [`docker`](https://docs.docker.com/install/linux/docker-ce/debian/#set-up-the-repository) and [`docker-compose`](https://docs.docker.com/compose/install/#install-compose)

1. Fork the [Wall-e Repo](https://github.com/CSSS/wall_e.git)  
2. Clone the repo
3. Wall_E Setting Specification.
   1. Wall_e needs parameter specifications. These are done via an [ini](https://en.wikipedia.org/wiki/INI_file) file. The biggest component this impacts is whether or not you use wall_e with a dockerized database. [Refer to the wiki page on the ini file](https://github.com/CSSS/wall_e/wiki/5.-contents-of-local.ini) for all the settings that wall_e reads from when doing local dev work.
      1. Ways to specify settings: (please note that all the following options require the ini file with the same structure located [here](https://github.com/CSSS/wall_e/wiki/5.-contents-of-local.ini) to be placed at location `wall_e/src/resources/utilities/config/local.ini`. This is so that wall_e know what settings it will be taking in, even if the values in the ini file do not indicate the actual values it will take in.)
         1. Specify via [Env variables](https://en.wikipedia.org/wiki/Environment_variable).
            1. Just export the settings [here](https://github.com/CSSS/wall_e/wiki/5.-contents-of-local.ini) with the specified values.
         2. Specify via [`wall_e/src/resources/utilities/config/local.ini`](https://github.com/CSSS/wall_e/wiki/5.-contents-of-local.ini).
            1. Be sure to **not** remove the headers on the ini. Also, please keep in mind that if you specify the same setting both via environment variable and via `.ini` file,  the environment variable will take precedence.
         3. Via `CI/user_scripts/docker-compose-mount-nodb.yml` or `CI/user_scripts/docker-compose-mount.yml`.
            1. Can be done following [these instructions](https://docs.docker.com/compose/environment-variables/#set-environment-variables-in-containers). Note that this is the same as via Env variables. The only difference is using this option will not result in the env variable be declared in your shell environment variable.
         4. As you may see from the link in the previous point, docker provides multiple ways to pass variables. You can use any that work for you.

    
*Keep in mind that unless otherwise indicated, all commands have to be run from `/path/to/repo/wall_e/src`*

You will need to recreate the base docker image if you made changes to any of the following files
 * wall_e/src/requirements.txt
 * CI/server_scripts/build_wall_e/Dockerfile.wall_e_base

#### With dockerized Wall-E
```shell
echo 'COMPOSE_PROJECT_NAME='"'"'discord_bot'"'"'' >  ../../CI/user_scripts/site_envs
. ../../CI/user_scripts/set_env.sh

echo 'POSTGRES_PASSWORD='"'"'daPassword'"'"'' >>  ../../CI/user_scripts/site_envs
echo 'ENVIRONMENT='"'"'LOCALHOST'"'"'' >>  ../../CI/user_scripts/site_envs
echo 'HOST='"'"${COMPOSE_PROJECT_NAME}_wall_e_db"'"'' >> ../../CI/user_scripts/site_envs
echo 'POSTGRES_PASSWORD='"'"'postgres_passwd'"'"'' >>  ../../CI/user_scripts/site_envs
. ../../CI/user_scripts/set_env.sh

if (you made changes to any of the files listed above){
    ../../CI/user_scripts/create-dev-docker-image.sh
    echo 'ORIGIN_IMAGE='"'"${COMPOSE_PROJECT_NAME}_wall_e_base"'"'' >>  ../../CI/user_scripts/site_envs
}else{
    echo 'ORIGIN_IMAGE='"'"'sfucsssorg/wall_e'"'"'' >>  ../../CI/user_scripts/site_envs

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

#### Running wall_e outside a docker container [to be able to Debug from Pycharm]
```shell
echo 'ENVIRONMENT='"'"'LOCALHOST'"'"'' >  ../../CI/user_scripts/site_envs
echo 'COMPOSE_PROJECT_NAME='"'"'discord_bot'"'"'' >>  ../../CI/user_scripts/site_envs
. ../../CI/user_scripts/set_env.sh

if (you are using a database){
    echo 'POSTGRES_PASSWORD='"'"'postgres_passwd'"'"'' >>  ../../CI/user_scripts/site_envs
    echo 'DB_PORT='"'"'5432'"'"'' >>  ../../CI/user_scripts/site_envs
    echo 'HOST='"'"'127.0.0.1'"'"'' >>  ../../CI/user_scripts/site_envs
}else{
    echo 'DB_ENABLED='"'"'0'"'"'' >>  ../../CI/user_scripts/site_envs
}
. ../../CI/user_scripts/set_env.sh

python3 -m pip install -r requirements.txt

if (you are using the dockerized database){
  docker run -d --env POSTGRES_PASSWORD=${POSTGRES_PASSWORD} -p "${DB_PORT}":5432 --name "${COMPOSE_PROJECT_NAME}_wall_e_db" postgres:alpine
  PGPASSWORD=$POSTGRES_PASSWORD psql -h "${HOST}" -U "postgres" -f WalleModels/create-database.ddl
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

```shell
./CI/user_scripts/test_walle.sh
```

### Step 2. Testing on [CSSS Bot Test Server](https://discord.gg/85bWteC)
After you have tested on your own Discord Test Server, create a PR to the [Wall-E Repo](https://github.com/CSSS/wall_e/pulls) that follows the [rules](https://github.com/CSSS/wall_e/wiki/3.-Making-a-PR-to-master) for PRs before pushing your changes to Wall-E. Creating the PR will automatically load it into the CSSS Bot Test Server. the name of the channel will be `pr-<PR number>`.  

## FAQs  

### Issue: Experiencing a networking issue with docker-compose

```shell

ERROR: could not find an available, non-overlapping IPv4 address pool among the defaults to assign to the network

```
resolution: If you are using a VPN, please disconnect and try again.
