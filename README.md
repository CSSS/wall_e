# CSSS Discord Bot (Wall-E)  

![The One and Only, Lovable Wall-E](wall_e_pic.jpg)

Wall-E, named after the lovable character [Wall-E](https://en.wikipedia.org/wiki/WALL-E), is the CSSS Discord Bot. This bot is owned by the CSSS and will be maintained by the current CSSS appointed Discord Manager and Bot_manager team. 


## Table of Contents
- [Software Engineering and Process Document](Software%20Engineering%20and%20Process%20Document)
- [Current Commands](#current-commands)  
- [How to work on the bot](Working_on_the_Bot.md)  
- [How to become a Bot_manager](Being_a_Bot_manager.md)

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
* `.here [<filter>]` - displays all users with permissions to view the current channel. Results can be filtered by looking for users whose username or nickname on the server contains the substring indicated with any of the included `<filter>` strings or all users if no filters are given. Multiple `<filters>` may be entered.
* `.poll <arg>` - starts a yes/no poll where `<arg>` is the question
* `.poll <arg0> <arg1> <arg2>` (up to 12 arguments) - starts a poll where `<arg0>` is the question and the remaining arguments are the options
* `.remindmein <arg0> to <arg1>` - created a reminder from `<arg0>` from now with the message `<arg1>`
* `showreminders` - displays all of the invoking user's reminders and their corresponding messageID
* `deletereminder <arg>` - deletes the reminder that the invoking user created that has the messageId `<arg>`
* `.urban <arg0>` - return definition from urban dictionary of `<arg0>`
* `.wolfram <arg>` - returns the result of passing `<arg>` to Wolfram Alpha
* `.urban <arg>` - returns defintion of `<arg>` along with a link to the definition on urban dictionary