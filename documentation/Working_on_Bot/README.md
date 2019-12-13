# Working on the Bot

- [Creating Bot and Attaching it to a Development Server](https://github.com/CSSS/wall_e/wiki/2.-Creating-Bot-and-Attaching-it-to-a-Development-Server)  
- [Running the Bot](https://github.com/CSSS/wall_e/wiki/3.-Running-the-Bot)  
- [Making a PR to master](https://github.com/CSSS/wall_e/wiki/4.-Making-a-PR-to-master)  
- [Test Cases](#test-cases)  
- [Reporting Issues](https://github.com/CSSS/wall_e/wiki/5.-Reporting-Issues)  
- [FAQs](#faqs)  


## Running the Bot
>If you encounter any errors doing the following commands, feel free to add it to the [FAQs section](documentation/Working_on_Bot#faqs) for future reference :)

Pre-requisites: `git` and `docker`.  

1. Fork the [Wall-e Repo](https://github.com/CSSS/wall_e.git)  
2. clone the repo
3. Wall_E Setting Specification.
   1. Wall_e needs some settings in order to determine how some parts should be treated. The biggest component this impacts is whether or not you use wall_e with or without a containerized container. [refer to the wiki page on the ini file](https://github.com/CSSS/wall_e/wiki/6.-contents-of-local.ini) for all the settings that wall_e reads from when doing local dev work.
      1. Ways to specify settings:
         1. Specify via Env varibles.
            1. Just export the settings [here](https://github.com/CSSS/wall_e/wiki/6.-contents-of-local.ini) with the specified values
         2. Specify via [`wall_e/src/resources/utilities/config/local.ini`](https://github.com/CSSS/wall_e/blob/use_pip_module/documentation/Working_on_the_Bot.md#localini).
            1. Be sure to not remove the headers on the ini. Also, please keep in mind that if you specify the same setting both via environment variable and via `.ini` file,  the environment variable will take precedence.
         3. Via `docker-compose-mount-nodb.yml` or `docker-compose-mount.yml`.
            1. Can be done following [these instructions](https://docs.docker.com/compose/environment-variables/#set-environment-variables-in-containers). Note that this is the same as via Env variables. The only difference is using this option will not result in the env variable be declared in your shell environment variable.
         4. As you may see from the link in the previous point, docker provides multiple ways to pass variables. You can use any that work for you.
4. Commands for the bot
> Due to some compatibility issues that occured in the past when wall_e was dockerized only on the server, the dev environment for wall_e was changed so that each developer doesn't have to fight with OS issues that come with some python modules that are a bit iffy. as long as you can get `docker` and `docker-compose` working, you are golden to work on wall_e.
### With the database

#### Step 1. Re-creating the database
You will need to recreate the base docker image if you
 * made changes to the wall_e/src/requirements.txt file or
 * made changes to the CI/server_scripts/Dockerfile.base file

Commands to Run
```shell
export CONTAINER_HOME_DIR=/usr/src/app;
export COMPOSE_PROJECT_NAME=whatever_you_want;
./CI/user_scripts/create-dev-docker-image.sh
```

#### Step 2. Launching the Bot
```shell
export ENVIRONMENT=LOCALHOST;

# if you did not need to re-create the base image you can use
export ORIGIN_IMAGE="sfucsssorg/wall_e"
# otherwise, you will need to use the below commmand
export ORIGIN_IMAGE="${COMPOSE_PROJECT_NAME}_wall_e_base"

export DB_ENABLED=1;

./CI/user_scripts/deploy-to-test-server.sh;
```

### Without the Database

#### Step 1. Re-creating the database
You will need to recreate the base docker image if you
 * made changes to the wall_e/src/requirements.txt file or
 * made changes to the CI/server_scripts/Dockerfile.base file

Commands To Run
```shell
export CONTAINER_HOME_DIR=/usr/src/app;
export COMPOSE_PROJECT_NAME=whatever_you_want;
./CI/user_scripts/create-dev-docker-image.sh
```

#### Step 2. Launching the Bot

#### Launching the bot
```shell
export ENVIRONMENT=LOCALHOST;
export DB_ENABLED=0;

# if you did not need to re-create the base image you can use
export ORIGIN_IMAGE="sfucsssorg/wall_e"
# otherwise, you will need to use the below commmand
export ORIGIN_IMAGE="${COMPOSE_PROJECT_NAME}_wall_e_base"

./CI/user_scripts/deploy-to-test-server-nodb.sh;
```

## Testing the bot

### Part 1. Run through the [linter](https://en.wikipedia.org/wiki/Lint_%28software%29)

Before you can push your changes to the wall_e repo, you will first need to make sure it passes the unit tests. that can be done like so:

```shell
docker build -t ${COMPOSE_PROJECT_NAME}_wall_e_test -f CI/Dockerfile.test --build-arg CONTAINER_HOME_DIR=/usr/src/app --build-arg UNIT_TEST_RESULTS=/usr/src/app/tests --build-arg TEST_RESULT_FILE_NAME=all-unit-tests.xml .
docker run -d --name ${COMPOSE_PROJECT_NAME}_test ${COMPOSE_PROJECT_NAME}_wall_e_test
docker logs ${COMPOSE_PROJECT_NAME}_test
```

### Part 2. Testing on [CSSS Bot Test Server](https://discord.gg/85bWteC)
After you have tested on your own Discord Test Server, Create a PR to the [Wall-E Repo](https://github.com/CSSS/wall_e/pulls) that follows the [rules](https://github.com/CSSS/wall_e/wiki/4.-Making-a-PR-to-master) for PRs before pushing your changes to [Wall-E](https://github.com/CSSS/wall_e). Creating the PR will automatically load it into the CSSS Bot Test Server. the name of the channel will be `pr-<PR number>`.  

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
  1. `.poll avengers?`## Local Setup  

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
I get the following issue when using docker-compose

`ERROR: could not find an available, non-overlapping IPv4 address pool among the defaults to assign to the network`

```
resolution: If you are using a VPN, please disconnect and try again.
