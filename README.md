# Wall-E  
  
![The One and Only, Lovable Wall-E](wall_e_pic.jpg) 

This repo will hold all the scripts for the upcoming bot that will operate on the csss discord, located [here](https://discord.gg/Pf5Ncq3). This bot is owned by the CSSS and will be maintained for the most part by the current CSSS appointed Discord representative and the current bot development team.
  
It is a namesake of the lovable [Wall-E](https://en.wikipedia.org/wiki/WALL-E).

## Local Setup

Follow these steps to run the bot and do development on your local machine.

### Part 1: Authentication

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

### Part 2: Running the Bot

Pre-requisites: `git`, `python3`, and `pip3`.

1. Run `git clone https://github.com/CSSS/wall_e.git && cd wall_e`
1. Run `pip3 install -r requirements.txt`
1. Edit `main.py` and replace `'YOUR_TOKEN_HERE'` with the token you previously obtained (within quotations)
1. Run `python3 main.py`
