# Working on the Bot

- [Wiki: Creating Bot and Attaching it to a Development Server](https://github.com/CSSS/wall_e/wiki/2.-Creating-Bot-and-Attaching-it-to-a-Development-Server)  
- [Running the Bot](#running-the-bot)  
  - [With the Database](#with-the-database)
    - [Step 1. Re-creating the docker base image](#step-1-re-creating-the-docker-base-image)
    - [Step 2. Launching the Bot](#step-2-launching-the-bot)
  - [Without the Database](#without-the-database)
    - [Step 1. Re-creating the docker base image](#step-1-re-creating-the-docker-base-image-1)
    - [Step 2. Launching the Bot](#step-2-launching-the-bot-1)
- [Testing the Bot](#testing-the-bot)
  - [Step 1. Run through the linter](#step-1-run-through-the-linter)
  - [Step 2. Testing on the CSSS Bot Test Server](#step-2-testing-on-csss-bot-test-server)
- [Wiki: Making a PR to master](https://github.com/CSSS/wall_e/wiki/3.-Making-a-PR-to-master)  
- [Test Cases](Test_Cases.md)  
- [Wiki: Reporting Issues](https://github.com/CSSS/wall_e/wiki/4.-Reporting-Issues)  
- [FAQs](#faqs)  


## Running the Bot
>If you encounter any errors doing the following commands, feel free to add it to the [FAQs section](#faqs) for future reference :)

> Due to some compatibility issue that occurs with some of the modules on some OSs, walL_e has been dockerized for both server-side running and local development. In order to work with wall_e, you need only `docker` and `docker-compose` working.

Pre-requisites: `git`, [`docker`](https://docs.docker.com/install/linux/docker-ce/debian/#set-up-the-repository) and [`docker-compose`](https://docs.docker.com/compose/install/#install-compose)

1. Fork the [Wall-e Repo](https://github.com/CSSS/wall_e.git)  
2. Clone the repo
3. Wall_E Setting Specification.
   1. Wall_e needs parameter specifications. These are done via an [ini](https://en.wikipedia.org/wiki/INI_file) file. The biggest component this impacts is whether or not you use wall_e with a dockerized database. [Refer to the wiki page on the ini file](https://github.com/CSSS/wall_e/wiki/5.-contents-of-local.ini) for all the settings that wall_e reads from when doing local dev work.
      1. Ways to specify settings: (please note that all the following options require the ini file with the same structure located [here](https://github.com/CSSS/wall_e/wiki/5.-contents-of-local.ini) to be placed at location `wall_e/src/resources/utilities/config/local.ini`. This is so that wall_e know what settings it will be taking in, even if the values in the ini file do not indicate the actual values it will take in.)
         1. Specify via [Env varibles](https://en.wikipedia.org/wiki/Environment_variable).
            1. Just export the settings [here](https://github.com/CSSS/wall_e/wiki/5.-contents-of-local.ini) with the specified values.
         2. Specify via [`wall_e/src/resources/utilities/config/local.ini`](https://github.com/CSSS/wall_e/wiki/5.-contents-of-local.ini).
            1. Be sure to **not** remove the headers on the ini. Also, please keep in mind that if you specify the same setting both via environment variable and via `.ini` file,  the environment variable will take precedence.
         3. Via `CI/user_scripts/docker-compose-mount-nodb.yml` or `CI/user_scripts/docker-compose-mount.yml`.
            1. Can be done following [these instructions](https://docs.docker.com/compose/environment-variables/#set-environment-variables-in-containers). Note that this is the same as via Env variables. The only difference is using this option will not result in the env variable be declared in your shell environment variable.
         4. As you may see from the link in the previous point, docker provides multiple ways to pass variables. You can use any that work for you.


### With the database

#### Step 1. Re-creating the docker base image
You will need to recreate the base docker image if you
 * made changes to the wall_e/src/requirements.txt file or
 * made changes to the CI/server_scripts/Dockerfile.base file

Commands to Run
```shell
export CONTAINER_HOME_DIR=/usr/src/app;
export COMPOSE_PROJECT_NAME="project_name"
 ./CI/user_scripts/create-dev-docker-image.sh
```

#### Step 2. Launching the Bot
```shell
export ENVIRONMENT=LOCALHOST;
//ensure that DB_ENBLED is set to 1 via whatever method you want
export COMPOSE_PROJECT_NAME="project_name"

# if you did not need to re-create the base image you can use
export ORIGIN_IMAGE="sfucsssorg/wall_e"
# otherwise, you will need to use the below commmand
export ORIGIN_IMAGE="${COMPOSE_PROJECT_NAME}_wall_e_base"

./CI/user_scripts/deploy-to-test-server.sh;
```

#### Re-launching the bot after making changes
```shell

## Stage 1: stop current bot
# enter the command `.exit` on your discord guild

## Stage 2: update base image
# if you made any new changes to the either of the files specified below,
 - wall_e/src/requirements.txt file
 - CI/server_scripts/Dockerfile.base file
# run the following commands:
export CONTAINER_HOME_DIR=/usr/src/app;
export COMPOSE_PROJECT_NAME="project_name"
 ./CI/user_scripts/create-dev-docker-image.sh


## Stage 3
./CI/user_scripts/deploy-to-test-server.sh;
```

#### view logs in active time
```shell
 docker logs -f "${COMPOSE_PROJECT_NAME}_wall_e"
```

### Without the Database

#### Step 1. Re-creating the docker base image
You will need to recreate the base docker image if you
 * made changes to the wall_e/src/requirements.txt file or
 * made changes to the CI/server_scripts/Dockerfile.base file

Commands To Run
```shell
export CONTAINER_HOME_DIR=/usr/src/app;
export COMPOSE_PROJECT_NAME="project_name"
./CI/user_scripts/create-dev-docker-image.sh
```

#### Step 2. Launching the Bot

```shell
export ENVIRONMENT=LOCALHOST;
//ensure that DB_ENBLED is set to 0 via whatever method you want
export COMPOSE_PROJECT_NAME="project_name"

# if you did not need to re-create the base image you can use
export ORIGIN_IMAGE="sfucsssorg/wall_e"
# otherwise, you will need to use the below commmand
export ORIGIN_IMAGE="${COMPOSE_PROJECT_NAME}_wall_e_base"

./CI/user_scripts/deploy-to-test-server-nodb.sh;
```


#### Re-launching the bot after making changes
```shell

## Stage 1: stop current bot
# enter the command `.exit` on your discord guild

## Stage 2: update base image
# if you made any new changes to the either of the files specified below,
 - wall_e/src/requirements.txt file
 - CI/server_scripts/Dockerfile.base file
# run the following commands:
export CONTAINER_HOME_DIR=/usr/src/app;
export COMPOSE_PROJECT_NAME="project_name"
 ./CI/user_scripts/create-dev-docker-image.sh


 ## Stage 3
./CI/user_scripts/deploy-to-test-server-nodb.sh;

```

#### view logs in active time
```shell
 docker logs -f "${COMPOSE_PROJECT_NAME}_wall_e"
```

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
