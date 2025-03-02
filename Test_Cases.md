# Test Cases

## Administration
  1. `/delete_log_channels`
  1. `/purge_messages`  
     ![](.documentation_pictures/test_cases/purge_messages.png)
  1. `.sync`  
     ![](.documentation_pictures/test_cases/.sync.png)
  1. `.announce "message"`  
     ![](.documentation_pictures/test_cases/.announce%20input.png)  
     Result:  
     ![](.documentation_pictures/test_cases/.announce%20result.png)
  1. `.announce "message" <messageId to reply to>`  
     ![](.documentation_pictures/test_cases/.announce%20follow-up%20input.png)  
     Result:  
     ![](.documentation_pictures/test_cases/.announce%20follow-up%20result.png)
  1. `/unload reminders`  
     ![](.documentation_pictures/test_cases/.unload%20reminders.png)
  1. `/unload nothing`  
     ![](.documentation_pictures/test_cases/.unload%20nothing.png)
  1. `/load reminders`  
     ![](.documentation_pictures/test_cases/.load%20reminders.png)
  1. `/load nothing`  
     ![](.documentation_pictures/test_cases/.load%20nothing.png)
  1. `/reload reminders`  
     ![](.documentation_pictures/test_cases/.reload%20reminders.png)
  1. `/reload nothing`  
     ![](.documentation_pictures/test_cases/.reload%20nothing.png)
  1. `.exc ls -l`  
     ![](.documentation_pictures/test_cases/.exc%20ls%20-l.png)
  1.  `.frequency`  
     ![](.documentation_pictures/test_cases/.frequency.png)
  1. `.frequency command`  
     ![](.documentation_pictures/test_cases/.frequency%20command.png)
## Ban
   1. `/convertbans`
   1. `/ban @user reason for my ban`
   1. `/ban @user "reason for my ban"`
   1. `/unban <id of banned user>`
   1. `/unban <id of not banned user>`
   1. `/unban <non integer something>`
   1. `/bans`
   1. `/purgebans`
## Frosh
   1. `.team`
   1. `.team "JL" "Super Tag" "Jon, Bruce, Clark, Diana, Barry"`
   1. `.team "team 1337" "PacMacro" "Jeffrey, Harry, Noble, Ali" "#E8C100"`
   1. `.team "Z fighters" "Cell Games" "Goku, Vegeta, Uub, Beerus" "4CD100"`
   1. `.team "spaces #1" "musical voice channels" "Billy, Bob, Megan, Cary" "notAHexCode"`
   1. `.reportwin`
   1. `.reportwin "team 1337" "Jeffrey, Harry, Noble, Ali"`
## HealthChecks
  1. `/ping`  
     ![](.documentation_pictures/test_cases/ping.png)
  1. `/echo this is the test case`  
     ![](.documentation_pictures/test_cases/echo%20this%20is%20the%20test%20case.png)
  1. `/echo "this is the test case"`  
     ![](.documentation_pictures/test_cases/echo%20%22this%20is%20the%20test%20case%22.png)
  1. `/echo 'this is the test case'`  
     ![](.documentation_pictures/test_cases/echo%20'this%20is%20the%20test%20case'.png)
## Help
  1. `.help`  
     ![](.documentation_pictures/test_cases/.help.png)
  1. `.help here`  
     ![](.documentation_pictures/test_cases/.help%20here.png)
  1. `.help nothing`  
     ![](.documentation_pictures/test_cases/.help%20nothing.png)
## Here
  1. `.here`  
     ![](.documentation_pictures/test_cases/.here.png)
  1. `.here wall`  
     ![](.documentation_pictures/test_cases/.here%20wall.png)
## Leveling
  1. `.set_level_name 1 XP_level_1`
     > if role `XP_level_1` exists
     
     ![](.documentation_pictures/test_cases/.set_level_name%201%20XP_level_1.png)
  1. `.set_level_name 1 XP`
     > where role `XP` does not exist
     
     ![](.documentation_pictures/test_cases/.set_level_name%201%20XP.png)
  1. `.remove_level_name 1`
     > when level 1 has a role
     
     ![](.documentation_pictures/test_cases/.a.remove_level_name%201.png)
  1. `.remove_level_name 1`
     > when level 1 does not have a role
     
     ![](.documentation_pictures/test_cases/.b.remove_level_name%201.png)
  1. `.rank`  
     ![](.documentation_pictures/test_cases/.rank.png)
  3. `.rank @other_user`  
     ![](.documentation_pictures/test_cases/.rank%20%40Micah.png)
  1. `.levels`  
     ![](.documentation_pictures/test_cases/.levels.png)
  1. `.ranks`  
     ![](.documentation_pictures/test_cases/.ranks.png)
  1. `.hide_xp`  
     ![](.documentation_pictures/test_cases/.a.hide_xp.png)
  1. `.hide_xp`
     > when your XP is already hidden
     
     ![](.documentation_pictures/test_cases/.hide_xp.png)
  1. `.show_xp`  
     ![](.documentation_pictures/test_cases/.b.show_xp.png)
  1. `.show_xp`
     > when your XP is already visible
     
     ![](.documentation_pictures/test_cases/.show_xp.png)
## Misc
  1. `.poll avengers?`  
     ![](.documentation_pictures/test_cases/.poll%20avengers%3F.png)
  1. `.poll`  
     ![](.documentation_pictures/test_cases/.poll.png)
  1. `.poll “go to the moon?” “yes” “no” “boye you crazy??”`  
     ![](.documentation_pictures/test_cases/.poll%20%22go%20to%20the%20moon%3F%22%20%22yes%22%20%22no%22%20%22boye%20you%20crazy%3F%3F%22.png)
  1. `.poll 1 2 3 4 5 6 7 8 9 10 11 12 13`  
     ![](.documentation_pictures/test_cases/.poll%201%202%203%204%205%206%207%208%209%2010%2011%2012%2013.png)
  1. `.urban girl`  
     ![](.documentation_pictures/test_cases/.urban%20girl.png)
  1. `.urban DevelopersDevelopersDevelopers`  
     ![](.documentation_pictures/test_cases/.urban%20DevelopersDevelopersDevelopers.png)
  1. `.wolfram Marvel`  
     ![](.documentation_pictures/test_cases/.wolfram%20Marvel.png)
  1. `.wolfram giberasdfasdfadfasdf`  
     ![](.documentation_pictures/test_cases/.wolfram%20giberasdfasdfadfasdf.png)
  1. `.emojispeak`  
     ![](.documentation_pictures/test_cases/.emojispeak.png)
  1. `.emojispeak 1234_abcd`  
     ![](.documentation_pictures/test_cases/.emojispeak%201234_abcd.png)
  1. `/tex e^{i\theta} = \cos x + i \sin x.png`
     ![](.documentation_pictures/test_cases/tex%20e%5E%7Bi%5Ctheta%7D%20%3D%20%5Ccos%20x%20%2B%20i%20%5Csin%20x.png)
## Mod
  1. `.em`
  1. `.em "description" "title" "field"`  
     ![](.documentation_pictures/test_cases/.em%20%22description%22%20%22title%22%20%22field%22.png)
  1. `.em "title" "field"`  
     ![](.documentation_pictures/test_cases/.em%20%22title%22%20%22field%22.png)
  1. `.warn`
  1. `.warn behold my mod powers and be scarred`  
     ![](.documentation_pictures/test_cases/.warn%20behold%20my%20mod%20powers%20and%20be%20scarred.png)
## Reminders
  1. `.remindmein`  
     ![](.documentation_pictures/test_cases/.remindmein.png)
  1. `.remindmein 10 seconds to turn in my assignment`  
     ![](.documentation_pictures/test_cases/a.remindmein%2010%20seconds%20to%20turn%20in%20my%20assignment.png)
     1. *wait 10 seconds*  
     ![](.documentation_pictures/test_cases/b.remindmein%2010%20seconds%20to%20turn%20in%20my%20assignment.png)
  1. `.remindmein 10 minutes to turn in my assignment`  
     ![](.documentation_pictures/test_cases/.remindmein%2010%20minutes%20to%20turn%20in%20my%20assignment.png)
  1. `.showreminders`  
     ![](.documentation_pictures/test_cases/a.showreminders.png)
  1. `.deletereminder <messageId from previous output>`  
     ![](.documentation_pictures/test_cases/.deletereminder%208.png)
  1. `.showreminders`  
     ![](.documentation_pictures/test_cases/b.showreminders.png)
  1. `.remindmeon <current day> <current time + 1 hour> to turn in my assignment`  
     ![](.documentation_pictures/test_cases/.remindmeon%20Oct%204%20at%206%3A23%20am%20to%20turn%20in%20my%20assignment.png)
  1. `.remindmeat tomorrow at 5:00pm Canada/Eastern to turn in my assignment`  
     ![](.documentation_pictures/test_cases/.remindmeat%20tomorrow%20at%205%3A00pm%20Canada%7CEastern%20to%20turn%20in%20my%20assignment.png)
  1. `.remindmein a day after tomorrow to turn in my assignment`  
     ![](.documentation_pictures/test_cases/.remindmein%20a%20day%20after%20tomorrow%20to%20turn%20in%20my%20assignment.png)
  1. `.showreminders`  
     ![](.documentation_pictures/test_cases/.showreminders.png)
## RoleCommands
  1. `/newrole <role that already exists>`  
     ![](.documentation_pictures/test_cases/newrole%20hello.png)
  1. `/newrole <new role>`  
     ![](.documentation_pictures/test_cases/newrole%20hello_5.png)
  1. `/iam <role that you do not have>`  
     ![](.documentation_pictures/test_cases/iam%201159103657120387167.png)
  1. `/iamn <role that you have>`  
     ![](.documentation_pictures/test_cases/iamn%201159103657120387167.png)
  1. `/deleterole <role that exists>`  
     ![](.documentation_pictures/test_cases/deleterole%201158444206990299208.png)
  1. `/whois <role with members>`  
     ![](.documentation_pictures/test_cases/whois%201007425263879069736.png)
  1. `/roles_assignable`  
     ![](.documentation_pictures/test_cases/roles_assignable.png)
  1. `/roles`  
     ![](.documentation_pictures/test_cases/roles.png)
  1. `/purgeroles`  
     ![](.documentation_pictures/test_cases/purgeroles.png)
## SFU
   1. `.sfu cmpt 300`  
     ![](.documentation_pictures/test_cases/.sfu%20cmpt%20300.png)
   1. `.sfu cmpt300`  
     ![](.documentation_pictures/test_cases/.sfu%20cmpt300.png)
   1. `.sfu cmpt666`  
     ![](.documentation_pictures/test_cases/.sfu%20cmpt666.png)
   1. `.sfu blah`  
     ![](.documentation_pictures/test_cases/.sfu%20blah.png)
   1. `.sfu`  
     ![](.documentation_pictures/test_cases/.sfu.png)
   1. `.outline cmpt300`  
     ![](.documentation_pictures/test_cases/.outline%20cmpt300.png)
   1. `.outline cmpt 300`  
     ![](.documentation_pictures/test_cases/.outline%20cmpt%20300.png)
   1. `.outline cmpt300 spring d200`  
     ![](.documentation_pictures/test_cases/.outline%20cmpt300%20spring%20d200.png)
   1. `.outline cmpt 300 spring d200`  
     ![](.documentation_pictures/test_cases/.outline%20cmpt%20300%20spring%20d200.png)
   1. `.outline cmpt300 next`  
     ![](.documentation_pictures/test_cases/.outline%20cmpt300%20next.png)
   1. `.outline cmpt300 d200 next`  
     ![](.documentation_pictures/test_cases/.outline%20cmpt300%20d200%20next.png)
   1. `.outline cmpt300 summer d200 next`  
     ![](.documentation_pictures/test_cases/.outline%20cmpt300%20summer%20d200%20next.png)
   1. `.outline cmpt666`  
     ![](.documentation_pictures/test_cases/.outline%20cmpt666.png)
   1. `.outline blah`  
     ![](.documentation_pictures/test_cases/.outline%20blah.png)
   1. `.outline`  
     ![](.documentation_pictures/test_cases/.outline.png)
   1. `/courses`  
     ![](.documentation_pictures/test_cases/courses.png)
   1. `/courses department:<existing department>`  
     ![](.documentation_pictures/test_cases/courses_department_math.png)
   1. `/courses department:<non existent department>`  
     ![](.documentation_pictures/test_cases/courses_department_blah.png)
   1. `/courses level:<number between 100-999>`  
     ![](.documentation_pictures/test_cases/courses_level_200.png)
   1. `/courses level:<number outside 100-999>`  
     ![](.documentation_pictures/test_cases/courses_level_1.png)
   1. `/courses term:<valid term> year:<valid year>`  
     ![](.documentation_pictures/test_cases/courses_term_and_year_set.png)
   1. `/courses term:<invalid term> year:<valid year>`  
     ![](.documentation_pictures/test_cases/courses_term_blah.png)
   1. `/courses term:<set> year:<unset>` OR `/courses term:<unset> year:<set>`  
     ![](.documentation_pictures/test_cases/courses_term_or_year_unset.png)
   1. `/courses department:<existent department> level:<valid number>`  
     ![](.documentation_pictures/test_cases/courses_department_math_level_200.png)
   1. `/courses department:<existent department> term:<valid term> year:<valid year>`  
     ![](.documentation_pictures/test_cases/courses_department_phys_term_summer_year_2020.png)
   1. `/courses level:<valid number> term:<valid term> year:<valid year>`  
     ![](.documentation_pictures/test_cases/courses_level_300_term_spring_year_2021.png)
   1. `/courses department:<existent department> level:<valid number> term:<valid term> year:<valid year>`  
     ![](.documentation_pictures/test_cases/courses_department_stat_level_300_term_fall_year_2024.png)
