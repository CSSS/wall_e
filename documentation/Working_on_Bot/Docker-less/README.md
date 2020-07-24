# Working on the Bot

- [Wiki: Creating Bot and Attaching it to a Development Server](https://github.com/CSSS/wall_e/wiki/2.-Creating-Bot-and-Attaching-it-to-a-Development-Server)  
- [Running the Bot without Docker](#running-the-bot-without-docker)  
  - [Launching the Bot](#launching-the-bot)
- [Testing the Bot](#testing-the-bot)
  - [Step 1. Run through the linter](#step-1-run-through-the-linter)
  - [Step 2. Testing on the CSSS Bot Test Server](#step-2-testing-on-csss-bot-test-server)
- [Wiki: Making a PR to master](https://github.com/CSSS/wall_e/wiki/3.-Making-a-PR-to-master)  
- [Test Cases](Test_Cases.md)  
- [Wiki: Reporting Issues](https://github.com/CSSS/wall_e/wiki/4.-Reporting-Issues)  
- [FAQs](#faqs)  


## Running the Bot without Docker
>If you encounter any errors doing the following commands, feel free to add it to the [FAQs section](#faqs) for future reference :)

Pre-requisites: `git`, `python3.8.5`

1. Fork the [Wall-e Repo](https://github.com/CSSS/wall_e.git)  
2. Clone the repo
3. Wall_E Setting Specification.
   1. Wall_e needs parameter specifications. These are done via an [ini](https://en.wikipedia.org/wiki/INI_file) file. The biggest component this impacts is whether or not you use wall_e with a dockerized database. [Refer to the wiki page on the ini file](https://github.com/CSSS/wall_e/wiki/5.-contents-of-local.ini) for all the settings that wall_e reads from when doing local dev work.
      1. Ways to specify settings: (please note that all the following options require the ini file with the same structure located [here](https://github.com/CSSS/wall_e/wiki/5.-contents-of-local.ini) to be placed at location `wall_e/src/resources/utilities/config/local.ini`. This is so that wall_e know what settings it will be taking in, even if the values in the ini file do not indicate the actual values it will take in.)
         1. Specify via [Env variables](https://en.wikipedia.org/wiki/Environment_variable).
            1. Just export the settings [here](https://github.com/CSSS/wall_e/wiki/5.-contents-of-local.ini) with the specified values.
         2. Specify via [`wall_e/src/resources/utilities/config/local.ini`](https://github.com/CSSS/wall_e/wiki/5.-contents-of-local.ini).
            1. Be sure to **not** remove the headers on the ini. Also, please keep in mind that if you specify the same setting both via environment variable and via `.ini` file,  the environment variable will take precedence.

#### Launching the Bot

*Keep in mind that unless otherwise indicated, all commands have to be run from the parent folder*

```shell
python3.8 -m virtualenv ENV
. ENV/bin/activate
mkdir logs
export ENVIRONMENT=LOCALHOST;
//ensure that DB_ENBLED is set to 0 via whatever method you want
python3.8 -m pip install -r requirements.txt
python3.8 wall_e/src/main.py
```

## Testing the bot

### Step 1. Run through the [linter](https://en.wikipedia.org/wiki/Lint_%28software%29)

Before you can push your changes to the wall_e repo, you will first need to make sure it passes the unit tests. that can be done like so:

```shell
python3.8 -m virtualenv testENV
. testENV/bin/activate
python3.8 -m pip install -r wall_e/test/test-requirements.txt
cp wall_e/test/pytest.ini wall_e/src/.
cp wall_e/test/validate-line-endings.sh wall_e/src/.
cp wall_e/test/setup.cfg wall_e/src/.
py.test --junitxml=test_results.xml wall_e/src
./wall_e/src/validate-line-endings.sh
```

### Step 2. Testing on [CSSS Bot Test Server](https://discord.gg/85bWteC)
After you have tested on your own Discord Test Server, create a PR to the [Wall-E Repo](https://github.com/CSSS/wall_e/pulls) that follows the [rules](https://github.com/CSSS/wall_e/wiki/3.-Making-a-PR-to-master) for PRs before pushing your changes to Wall-E. Creating the PR will automatically load it into the CSSS Bot Test Server. the name of the channel will be `pr-<PR number>`.  

## FAQs  
