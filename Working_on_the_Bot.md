# Working on the Bot

## Local Setup

Follow the steps below setup your test discord guild, to run the bot and do development on your local machine.  

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

1. Fork the [Wall-e Repo](https://github.com/CSSS/wall_e.git)
1. From a command line
1. Run `git clone <the url of your forked repo>`
1. cd into `wall_e` directory
1. Run `python3.5 -m venv ENV`
1. Run `. ENV/bin/activate`
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
   1. Run `export WOLFRAMAPI=apikey` with an API key obtained from [here](https://products.wolframalpha.com/api/)
      1. You can also do `export WOLFRAMAPI='dev'` if you dont want to open a WolframAlpha account [this doesnt work if you need to do work that involves the `.wolfram` command]
   1. Run `python3.5 main.py`
1. Testing on [CSSS Bot Test Server](https://discord.gg/85bWteC)
   1. After you have tested on your own Discord Test Server, push your changes to [Wall-E](https://github.com/CSSS/wall_e). Pushing it will automatically load it into the CSSS Bot Test Server. the name of the channel will be `pr-<PR number>`.
1. Run `python3.5 main.py`

## Making a PR to master

These are the things you need to ensure are cover in your PR, otherwise the CODEOWNERS will not approve your PR, not matter how much you ping them to do so on the Discord
 1. The description in the PR is a fair representation of what the PR is about.
 1. The PR is fixing one thing and one thing only.
 1. Logging. if you have N variables initialzed/used in your function, you should print all of them out to the log using logging module at least once or have a good reason why you arent.
 1. If your PR is doing something like adding a new line or removing a new line, CODEOWNERS reserve the right to ask that you undo that change unless it was for a specific reason.
 1. 
 1. If you are adding a new command....**document**. Document the following things on help.json and the README.md
    1. The purpose of the command
    1. If the argument is called with any arguments.
       1. If it is called with any arguments, please either provide a good enough explanation of the arg that a user can tell what it will do before using the command. adding an example of how to call it with the args is not necessary but good practice.
 1. If you are making a new Class of commands, add the class to bot.json following the convention already there.
 1. Evidence of Testing. This one needs to be completed after the PR is opened, at that point, you will go on the channel on the CSSS Wall-E Test Server that was automatically created when the PR was opened and then test the following functionality. Once you had done so, you can leave a comment on the PR stating that you had done the necessary testing.
 1. Please provide ways to test whatever you just modified on the bot so that future PRs can be tested to ensure they dont break *your code* when merging to master
 
 ### Test Cases
 `.ping`
 `.echo this is the test case`
 `.help`
   Please ensure that the pagination is not effected by doing the following
      go to the last page and then hit next when on the last page to make sure it goes back to the beginning
      go to the last page from the first page by hitting previous
      make sure that the done emoji does delete the help output
`.here`
`.here k`
`.poll`
`.poll "question"`
`.poll question answer1 answer 2`
`.urban yo`
`.wolfram 1+1`
`.remindmein 20 seconds to test`
`.showreminders`
`.deletereminder <output from showreminder>`
`.remindmein 10 seconds to test`  
   wait 10 seconds to ensure that it did delete
`.iam <whatever_name_you_want_to_use>`
`.newrole <whatever_name_you_want_to_use>`
`.whois <whatever_name_you_want_to_use>`
`.iam <whatever_name_you_want_to_use>`
`.whois <whatever_name_you_want_to_use>`
`.deleterole <whatever_name_you_want_to_use>`
`.iamn <whatever_name_you_want_to_use>`
`.whois <whatever_name_you_want_to_use>`
`.deleterole <whatever_name_you_want_to_use>`
`.roles`
`.Roles`
 ## Reporting Issues

 If you come across issues that googling wont solve, you can email the bot-managers with the details at `csss-bot-manager@sfu.ca`. Please note that if your email is not detailed enough, the bots may not necessarily respond. Please over-provide rather than under-provide.