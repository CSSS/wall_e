# CSSS Discord Bot (Wall-E)  

![The One and Only, Lovable Wall-E](wall_e_pic.jpg) 

Wall-E, named after the lovable character [Wall-E](https://en.wikipedia.org/wiki/WALL-E), will hold all the scripts for the upcoming bot that will operate on the CSSS discord, located [here](https://discord.gg/Pf5Ncq3). This bot is owned by the CSSS and will be maintained by the current CSSS appointed Discord representative and the current bot development team. 


## Table of Contents
- [Software Engineering and Process Document](Software%20Engineering%20and%20Process%20Document)
- [Current Commands](#current-commands)  
- [Local Setup](#local-setup)  
- [Current-Setup Info](#current-setup-info)  
- [Part 1: Authentication](#part-1-authentication)  
- [Part 2: Running the bot](#part-2-running-the-bot)

## Current Commands

* `.help` - shows the list of available commands
* `.ping` - returns `pong!`
* `.echo <arg>` - returns `<arg>`
* `.newrole <arg>` - creates role `<arg>`
* `.deleterole <arg>` - deletes role `<arg>`
* `.iam <arg>` - adds you to role `<arg>`
* `.iamn <arg>` - removes you from role `<arg>`
* `.whois <arg>` - returns everyone who has role `<arg>`
* `.roles` - displays all roles that exist on the server
* `.poll <arg>` - starts a yes/no poll where `<arg>` is the question
* `.poll <arg0> <arg1> <arg2>` (up to 12 arguments) - starts a poll where `<arg0>` is the question and the remaining arguments are the options
* `.remindmein <arg0> to <arg1>` - created a reminder from `<arg0>` from now with the message `<arg1>`
* `showreminders` - displays all of the invoking user's reminders and their corresponding messageID
* `deletereminder <arg>` - deletes the reminder that the invoking user created that has the messageId `<arg>`
* `.urban <arg0>` - return definition from urban dictionary of `<arg0>`

## Local Setup

#### Current-Setup Info  
Server IP: 178.128.184.141    
For access to the jenkins, notify someone on the following list:  
* Winfield Chen (CSSS VP) - csss-vp@sfu.ca  

Follow steps outlined in the [README for machine setup](files_for_machine_setup) steps to prepare the host machine to support CI/CD

Follow these steps to run the bot and do development on your local machine.  

### Part 1: Creating Bot and Attaching it to Development Server

1. Create your own Discord server for testing by
   1. Going to `https://discordapp.com/channels/@me`
   2. Clicking the + on the left side 

   ![Creating Discord Development Server](README_files/create_development_server.png) 

2. Navigate to `https://discordapp.com/developers/applications/me` and login
3. Click `Create New Application` 

![Creating Discord Application](README_files/create_application.png) 
4. Change the name of the Application to whatever you want and then click `Save Changes`
5. Take note of the `Client ID` for step 8
6. Click on `Bot` 

![Click on Bot](README_files/click_on_bot.png) 
7. Click on `Add Bot` 

![Click on Add Bot](README_files/add_bot.png)  
8. Navigate to `https://discordapp.com/oauth2/authorize?&client_id=YOUR_CLIENT_ID_HERE&scope=bot&permissions=2119564375`
   * `YOUR_CLIENT_ID` is the `CLIENT ID` you recorded in Step 5
9. Select the server you created and click `Authorize`

### Part 2: Running the Bot

Pre-requisites: `git`, `python3.5`, and `pip3`.

From a command line
1. Run `git clone https://github.com/CSSS/wall_e.git`
1. cd into `wall_e` directory
1. Run `python3.5 -m pip install -r requirements.txt`
1. Redis Instructions
   1. Mac
      1. Run `brew install redis`
      1. Add `notify-keyspace-events "Ex"` to the end of `/usr/local/etc/redis.conf`
      1. Run `brew services start|stop|restart redis` to start, stop and restart redis
   1. Ubuntu
      1. Run `sudo apt-get install -y redis-server`
      1. Add `notify-keyspace-events "Ex"` to the end of `/etc/redis/redis.conf`
      1. Run `sudo service redis-server start`
1. Using Your Own Discord Test Server
   1. Run `export ENVIRONMENT='localhost'`
   1. Run `export TOKEN=token` with the `token` you obtained during the authentication step
   1. Run `export BOT_LOG_CHANNEL_ID=channel_id` with the channel id of the channel that will hold the logs on the discord server
   1. Run `python3.5 main.py`
1. Testing on [CSSS Bot Test Server](https://discord.gg/c3MPjY5)
   1. After you have tested on your own Discord Test Server, push your changes to [Wall-E](https://github.com/CSSS/wall_e). Pushing it will automatically load it into the CSSS Bot Test Server
