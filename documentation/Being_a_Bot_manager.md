# Being a Bot_manager

## Becoming a Bot_manager  

1. Get added to the CODEOWNERS file  
1. Perms you need to get from existing Bot_managers  
   1. Account on [Wall-E's Jenkins Server](178.128.184.141)  
   1. Password to `csss-bot-manager@sfu.ca` which gives you admin portal access to Wall-E on discord.  

## Things to get familiar with:

1. Wall-E's Jenkins Server: [178.128.184.141](178.128.184.141)  
   1. To request access, please send an email to `csss-bot-manager@sfu.ca` which states your name and what is the reason for you wanting access.  

1. Checklist of what to look for before approving a PR to master  
   1. the description of the PR is a fair representation of what it is for  
   1. The PR is fixing only one thing.  
   1. not enough logging, if the code has N variables initialized/used in the function, it should print all of them out to the log at least once or have a good reason why they arent arent.  
   1. If the PR is doing something like adding a new line or removing a new line, we reserve the right to ask that they undo that change unless it was for a specific reason.
   1. if the PR are adding a new command, documentation is needed of the following things
      1. the purpose of the command  
      1. if its called with any arguments  
         1. if it is, they need to either provide a good enough explanation of the arg that a user can tell what it will do before using the command. adding an example of how to call it with the args is not necessary but good practice.  

In the event that the host server needs to be replicated, plase follow the steps outlined in the [README for machine setup](files_for_machine_setup) steps to prepare the host machine to support CI/CD.
