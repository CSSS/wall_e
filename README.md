# CSSS Discord Bot (Wall-E)  

![The One and Only, Lovable Wall-E](wall_e_pic.jpg)

Wall-E, named after the lovable character [Wall-E](https://en.wikipedia.org/wiki/WALL-E), is the CSSS Discord Bot. This bot is owned by the CSSS and will be maintained by the current CSSS appointed Discord Manager and Bot_manager team.


## Table of Contents
- [Software Engineering and Process Document](documentation/Software%20Engineering%20and%20Process%20Document)
- [Current Commands](#current-commands)  
- [How to work on the bot](documentation/Working_on_the_Bot.md)  
- [How to become a Bot_manager](documentation/Being_a_Bot_manager.md)

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
* `.purgeroles` - purges empty self-assignable roles
* `.here [<filter>]` - displays all users with permissions to view the current channel. Results can be filtered by looking for users whose username or nickname on the server contains the substring indicated with any of the included `<filter>` strings or all users if no filters are given. Multiple `<filters>` may be entered.
* `.poll <arg>` - starts a yes/no poll where `<arg>` is the question
* `.poll <arg0> <arg1> <arg2> ... <arg11>` (up to 12 arguments) - starts a poll where `<arg0>` is the question and the remaining arguments are the options
* `.remindmein <arg0> <units> to <arg1>` - created a reminder for `<arg0>` units from now with the message `<arg1>`, where units can be seconds, minutes, hours, days, months, or years.
   * Usage examples:
      * `.remindmein 10 minutes to do homework`
      * `.remindmein 2 hours to do laundry`
      * `.remindmein 5 days to finish assignment`
      
* `showreminders` - displays all of the invoking user's reminders and their corresponding messageID
* `deletereminder <arg>` - deletes the reminder that the invoking user created that has the messageId `<arg>`
* `.urban <arg>` - return definition from urban dictionary of `<arg>`
* `.wolfram <arg>` - returns the result of passing `<arg>` to Wolfram Alpha
* `.urban <arg>` - returns defintion of `<arg>` along with a link to the definition on urban dictionary
* `.sfu <arg0>` - returns calendar description from current semesters calendar of `<arg0>`
* `.outline <arg0> [<arg1> <arg2>]` - returns outline details of course `<arg0>`. Defaults to current term and section d100. Optionally, you may specify term in `<arg1>` and/or section with `<arg2>`. 
    * Usage examples:
    * `.outline cmpt300`
    * `.outline cmpt300 d200`
    * `.outline cmpt300 spring`
    * `.outline cmpt300 summer d200`
