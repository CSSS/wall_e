# Working on the Bot

- [1. Setup Python Environment](#1-setup-python-environment)
- [2. Setup and run Wall-E](#2-setup-and-run-wall-e)
- [3. Before opening a PR](#2-setup-and-run-wall-e)
- [4. Testing on CSSS Bot Test Server](#2-setup-and-run-wall-e)
- [Wiki: Making a PR to master](https://github.com/CSSS/wall_e/wiki/3.-Making-a-PR-to-master)  
- [Test Cases](Test_Cases.md)  
- [Wiki: Reporting Issues](https://github.com/CSSS/wall_e/wiki/4.-Reporting-Issues)  
- [FAQs](#faqs)  


## 1. Setup Python Environment

### for Debian based OS
```shell
sudo apt-get install -y python3.9
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3.9 get-pip.py --user
python3.9 -m pip install virtualenv --user
python3.9 -m virtualenv walle
. walle/bin/activate
```

### for MacOS
open to anyone to make a PR adding this section

### for Windows
open to anyone to make a PR adding this section

## 2. Setup and run Wall-E
>If you encounter any errors doing the following commands, feel free to add it to the [FAQs section](#faqs) for future reference :)

Pre-requisites: `git`
```shell
If you hve not cloned your forked version yet
wget https://raw.githubusercontent.com/CSSS/wall_e/master/download_repo.sh
./download_repo.sh

If you have forked your version
./run_site.sh
```

### 2.1 To make any needed changes to the models
```shell
python -m pip uninstall wall_e_models

git clone https://github.com/CSSS/wall_e_models.git
cd wall_e_models
# make any necessary changes

# package model
python3 setup.py sdist

# install package for wall_e
python -m pip install ../wall_e_models/dist/wall_e_models-0.X.tar.gz
```

How the Variable needs to be initialized [only relevant to you if you like granularized variable initializations]
| Variable             |   Dockerized |            |           | Non-Dockerized |           |
|----------------------|--------------|------------|-----------|----------------|-----------|
|                      | env variable | wall_e.env | local.ini | env variable   | local.ini |
| ENVIRONMENT          |              |      X     |           | x              |           |
| COMPOSE_PROJECT_NAME |         X    |            |           | X              |           |
| POSTGRES_PASSWORD    |         X    |      X     |           | x              |           |
| DOCKERIZED           |              |      -     |    -      | -              |     -     |
| WALL_E_DB_USER       |              |      X     |           | x              |           |
| WALL_E_DB_PASSWORD   |              |      X     |           | x              |           |
| WALL_E_DB_DBNAME     |              |      X     |           | x              |           |
| DB_ENABLED           |              |      -     |    -      | -              |     -     |
| HOST                 |              |      -     |    -      | x              |           |
| ORIGIN_IMAGE         |        X     |            |           |                |           |
| BOT_LOG_CHANNEL      |              |      -     |    -      | -              |     -     |
| BOT_GENERAL_CHANNEL  |              |      -     |    -      | -              |     -     |
| DB_PORT              |              |      X     |           | X              |           |


> X indicates that its necessary to be declared in that way  
> '-' indicates that the user can choose to declare it only that way

## 3. Before opening a PR

Please submit PRs one week before they need to be merged.

### 3.1. Validating the code

```shell
../../CI/user_scripts/test_walle.sh
```

## 4. Testing on [CSSS Bot Test Server](https://discord.gg/85bWteC)
After you have tested on your own Discord Test Guild, create a PR to the [Wall-E Repo](https://github.com/CSSS/wall_e/pulls) that follows the [rules](https://github.com/CSSS/wall_e/wiki/3.-Making-a-PR-to-master) for PRs before pushing your changes to Wall-E. Creating the PR will automatically load it into the CSSS Bot Test Server. the name of the channel will be `pr-<PR number>`.  

## FAQs  

### Issue: Experiencing a networking issue with docker-compose

```shell

ERROR: could not find an available, non-overlapping IPv4 address pool among the defaults to assign to the network

```
resolution: If you are using a VPN, please disconnect and try again.
