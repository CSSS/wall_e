# Test Cases

## Administration
  1. `.unload reminders`
  1. `.unload nothing`
  1. `.load reminders`
  1. `.load nothing`
  1. `.reload reminders`
  1. `.reload nothing`
  1. `.exc ls -l`
  1.  `.frequency`
  1. `.frequency command`
## HealthChecks
  1. `.ping`
  1. `.echo this is the test case`
  1. `.echo "this is the test case"`
  1. `.echo 'this is the test case'`
## Here
  1. `.here`
  1. `.here wall`
## Misc
  1. `.poll avengers?`
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
     1. Please ensure that the pagination is not affected by doing the following
        1. go to the last page and then hit next when on the last page to make sure it goes back to the beginning
        1. go to the last page from the first page by hitting previous
        1. make sure that the done emoji does delete the help output
  1. `.help here`
  1. `.help nothing`
## Mod

## Reminders
  1. `.remindmein`
  1. `.remindmein 10 seconds to turn in my assignment`
     1. *wait 10 seconds*
  1. `.remindmein 10 minutes to turn in my assignment`
  1. `.showreminders`
  1. `.deletereminder <messageId from previous output>`
  1. `.showreminders`
  1. `.remindmeon <current day> <current time + 1 hour> to turn in my assignment`
  1. `.remindmeat tomorrow at 5:00pm Canada/Eastern to turn in my assignment`
  1. `.remindmein a day after tomorrow to turn in my assignment`
  1. `.showreminders`
  1. `.deletereminder` for the reminders entered above
## RoleCommands
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
## SFU
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
## Frosh
   1. `.team`
   1. `.team "JL" "Super Tag" "Jon, Bruce, Clark, Diana, Barry"`
   1. `.team "team 1337" "PacMacro" "Jeffrey, Harry, Noble, Ali" "#E8C100"`
   1. `.team "Z fighters" "Cell Games" "Goku, Vegeta, Uub, Beerus" "4CD100"`
   1. `.team "spaces #1" "musical voice channels" "Billy, Bob, Megan, Cary" "notAHexCode"`
   1. `.reportwin`
   1. `.reportwin "team 1337" "Jeffrey, Harry, Noble, Ali"`
## Ban
   1. `.initban`
   1. `.ban @user reason for my ban`
   1. `.ban @user "reason for my ban"`
   1. `.ban @user @user1 reason`
   1. `.ban @user @user1 "reason blah"`
   1. `.unban <id of banned user>`
   1. `.unban <id of not banned user>`
   1. `.unabn <non integer something>
   1. `.bans`