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
- [Test Cases](#test-cases)  
- [Wiki: Reporting Issues](https://github.com/CSSS/wall_e/wiki/4.-Reporting-Issues)  
- [FAQs](#faqs)  


## Running the Bot
>If you encounter any errors doing the following commands, feel free to add it to the [FAQs section](#faqs) for future reference :)

> Due to some compatibility issue that occurs with some of the modules on some OSs, walL_e has been dockerized for both server-side running and local development. In order to work with wall_e, you need only `docker` and `docker-compose` working.

Pre-requisites: `git`, [`docker`](https://docs.docker.com/install/linux/docker-ce/debian/#set-up-the-repository) and [`docker-compose`](https://docs.docker.com/compose/install/#install-compose)

1. Fork the [Wall-e Repo](https://github.com/CSSS/wall_e.git)  
2. Clone the repo
3. Wall_E Setting Specification.
   1. Wall_e needs some settings in order to determine which commands should be enabled. The biggest component this impacts is whether or not you use wall_e with a dockerized database. [Refer to the wiki page on the ini file](https://github.com/CSSS/wall_e/wiki/5.-contents-of-local.ini) for all the settings that wall_e reads from when doing local dev work.
      1. Ways to specify settings: (please note that all the following options require the ini file with the same structure located [here](https://github.com/CSSS/wall_e/wiki/5.-contents-of-local.ini) to be placed at location `wall_e/src/resources/utilities/config/local.ini`. This is so that wall_e know what settings it will be taking in, even if the values in the ini file do not indicate the actual values it will take in.)
         1. Specify via Env varibles.
            1. Just export the settings [here](https://github.com/CSSS/wall_e/wiki/5.-contents-of-local.ini) with the specified values.
         2. Specify via [`wall_e/src/resources/utilities/config/local.ini`](https://github.com/CSSS/wall_e/wiki/5.-contents-of-local.ini).
            1. Be sure to not remove the headers on the ini. Also, please keep in mind that if you specify the same setting both via environment variable and via `.ini` file,  the environment variable will take precedence.
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

## Test Cases  

### Administration  
  1. `.unload reminders`
  1. `.unload nothing`
  1. `.load reminders`
  1. `.load nothing`
  1. `.reload reminders`
  1. `.reload nothing`
  1. `.exc ls -l`
  1.  `.frequency`
  1. `.frequency command`  
### HealthChecks  
  1. `.ping`  
  1. `.echo this is the test case`
  1. `.echo "this is the test case"`
  1. `.echo 'this is the test case'`
### Here  
  1. `.here`
  1. `.here wall`
### Misc  
  1. `.poll avengers?`
  1. `.poll`
  1. `.poll “go to the moon?” “yes” “no” “boye you crazy??”`
  1. `.poll 1 2 3 4 5 6 7 8 9 10 11 12 13`
  1. `.urban girl`
  1. `.urban DevelopersDevelopersDevelopers`
  1. `.wolfram Marvel`
  1. `.wolfram giberasdfasdfadfasdf`
  1. `.emojispeak`
  1. `.emojispeak 1234_abcd`
  1. `.help`  
     1. Please ensure that the pagination is not effected by doing the following  
        1. go to the last page and then hit next when on the last page to make sure it goes back to the beginning  
        1. go to the last page from the first page by hitting previous  
        1. make sure that the done emoji does delete the help output  
  1. `.help here`
  1. `.help nothing`
### Mod

### Reminders
  1. `.remindmein`
  1. `.remindmein 10 seconds to turn in my assignment`
     1. *wait 10 seconds*
  1. `.remindmein 10 minutes to turn in my assignment`
  1. `.showreminders`
  1. `.deletereminder <messageId from previous output>`
  1. `.showreminders`
### RoleCommands
  1. `.newrole`
  1. `.newrole <role that already exists>`
  1. `.newrole <new role>`
  1. `.iam`
  1. `.iam <role that you already have>`
  1. `.iam <role that you do not have>`
  1. `.iamn`
  1. `.iamn <role that you have>`
  1. `.iamn <role that you dont have>`
  1. `.deleterole`
  1. `.deleterole <role that does not exist>`
  1. `.deleterole <role that exists>`
  1. `.whois`
  1. `.whois <role with no people>`
  1. `.whois <role with members>`
  1. `.whois <role that does not exist>`
  1. `.roles`
  1. `.Roles`
  1. `.purgeroles`
### SFU
   1. `.sfu cmpt 300`
   1. `.sfu cmpt300`
   1. `.sfu cmpt666`
   1. `.sfu blah`
   1. `.sfu`
   1. `.outline cmpt300`
   1. `.outline cmpt 300`
   1. `.outline cmpt300 spring d200`
   1. `.outline cmpt 300 spring d200`
   1. `.outline cmpt300 next`
   1. `.outline cmpt300 d200 next`
   1. `.outline cmpt300 summer d200 next`
   1. `.outline cmpt666`
   1. `.outline blah`
   1. `.outline`

## FAQs  

### Issue: Experiencing a networking issue with docker-compose

```shell

`ERROR: could not find an available, non-overlapping IPv4 address pool among the defaults to assign to the network`

```
resolution: If you are using a VPN, please disconnect and try again.
