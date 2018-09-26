# Working on the Bot

## Local Setup

Follow the steps below [Part 1] to run the bot and do development on your local machine.  

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

Pre-requisites: `git`, `python3`, `python3-venv`, and `python3-pip`.

From a command line
1. Run `git clone https://github.com/CSSS/wall_e.git`
2. cd into `wall_e` directory
3. Run `python3.5 -m venv ENV`
4. Run `. ENV/bin/activate`
5. Run `python3.5 -m pip install -r requirements.txt`
6. Run `sudo apt-get install -y redis-server`
7. Edit `/etc/redis/redis.conf` to add line `notify-keyspace-events "Ex"`
8. Run `sudo service redis-server start`
9. Run `export TOKEN=token` with the `token` you obtained during the authentication step
10. Run `python3.5 main.py`