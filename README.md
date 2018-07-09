# Wall-E  
  
![The One and Only, Lovable Wall-E](wall_e_pic.jpg) 

This repo will hold all the scripts for the upcoming bot that will operate on the CSSS discord, located [here](https://discord.gg/Pf5Ncq3). This bot is owned by the CSSS and will be maintained for the most part by the current CSSS appointed Discord representative and the current bot development team.
  
It is a namesake of the lovable [Wall-E](https://en.wikipedia.org/wiki/WALL-E).
  
## Table of Contents
 - [Current Commands](#current-commands)
 - [Local Setup](#local-setup)
       - [Current-Setup Info](#current-setup-info)
    - [Part 1: Server Setup](#part-1-server-setup)
       - [Jenkins Setup on Docker](#jenkins-setup-on-docker)
    - [Part 2: Authentication](#part-2-authentication)
    - [Part 3: Running the bot](#part-3-running-the-bot)  
  
## Current Commands

* `.ping` - returns `pong!`
* `.echo <arg>` - returns `<arg>`
* `.newrole <arg>` - creates role `<arg>`
* `.iam <arg>` - adds you to role `<arg>`
* `.iamn <arg>` - removes you from role `<arg>`
* `.whois <arg>` - returns everyone who has role `<arg>`
* `.poll <arg>` - starts a yes/no poll where `<arg>` is the question
* `.poll <arg0> <arg1> <arg2>` (up to 12 arguments) - starts a poll where `<arg0>` is the question and the remaining arguments are the options

## Local Setup
  
#### Current-Setup Info  
Server IP: 178.128.184.141    
For access to the jenkins, notify someone on the following list:  
 * Winfield Chen (CSSS VP) - csss-vp@sfu.ca  

Follow these steps to run the bot and do development on your local machine.  
  
### Part 1: Server Setup  
  
#### Jenkins Setup on Docker
 1. Spin-up a linux server [This documentation was made with an Ubuntu 16.04.4 server]  
 2. run the following command  
```shell
./setup_environment_for_wall_e.sh
```
the above script was adapted from the commandline history gleamed from the commands used by the person who set up the server. If you encounter issues with the script, feel free to look at the command history instead at [command history.txt](files_for_machine_setup/command_history.txt)  
 3. docker container should end up being set up with  
   1. `Python 3.5.5`  
   2. `pip 10.0.1 from /usr/local/lib/python3.5/site-packages/pip (python 3.5)`  

#### Nginx Set-up
 1. Compare the `/etc/nginx/sites-enabled/default` file on the machine vs the [default](files_for_machine_setup/default) file included in this repo to see if the server copy needs any changes.
 1. Run `nginx -t` to test the configuration file.
 1. If tests pass, run `sudo service nginx restart `
  
#### Redis setup
 1. Compare the `/etc/redis/redis.conf` file on the machine vs the [redis.conf](files_for_machine_setup/redis.conf) file included in this repo to see if the server copy needs any changes.
 2. Misc. Commands that may be useful for this step
   1. `sudo service redis-server restart`
   2. `redis-cli --csv subscribe '__keyevent@0__:expired'`
   3. `docker ps`
   4. `docker stop wall-e-test`
   5. `docker logs -f wall-e-test`
   6. `docker start wall-e-test`
   7. `docker rm wall-e-test `

### Part 2: Authentication

Pre-requisites: A Discord account.

1. Create your own Discord server for testing
1. Navigate to `https://discordapp.com/developers/applications/me` and login
1. Click `New App`
1. Name your app to whatever you wish then click `Create App`
1. Save the `Client ID` under the `App Details`
1. Scroll down, click `Create a Bot User` and confirm
1. Within the new `Bot` section of the dashboard, click `click to reveal`, and save the token
1. Naviate to `https://discordapp.com/oauth2/authorize?&client_id=YOUR_CLIENT_ID_HERE&scope=bot&permissions=0` and replace `YOUR_CLIENT_ID_HERE` with the client ID of your bot
1. Select the server you created and click `Authorize`

### Part 3: Running the Bot

Pre-requisites: `git`, `python3`, and `pip3`.

1. Run `git clone https://github.com/CSSS/wall_e.git && cd wall_e`
1. Run `pip3 install -r requirements.txt`
1. Run `TOKEN=` the token you previously obtained
1. Run `python3 main.py`
