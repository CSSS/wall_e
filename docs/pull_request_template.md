## PR Checklist

### Description:  
  
  
### Things to Cover:  
These are the things you need to ensure are covered in your PR, otherwise the CODEOWNERS will not approve your PR, not matter how much you ping them to do so on the Discord  
  
 1. The description in the PR is a fair representation of what the PR is about.
 1. The PR is fixing one thing and one thing only.
 1. Logging. if you have N variables initialzed/used in your function, you should print all of them out to the log using logging module at least once or have a good reason why you arent.
 1. If your PR is doing something like adding a new line or removing a new line, CODEOWNERS reserve the right to ask that you undo that change unless it was for a specific reason.
 1. If you are adding a new command....document. Document the following things on help.json and the README.md
    1. The purpose of the command
    1. If the argument is called with any arguments.
       1. If it is called with any arguments, please either provide a good enough explanation of the arg that a user can tell what it will do before using the command. adding an example of how to call it with the args is not necessary but good practice.
 1. If you are making a new Class of commands, add the class to bot.json following the convention already there.
 1. Evidence of Testing. This one needs to be completed after the PR is opened. At that point, you will go on the channel on the CSSS Wall-E Test Server that was automatically created when the PR was opened and then test the [following functionality](https://github.com/CSSS/wall_e/blob/master/documentation/Working_on_Bot/Test_Cases.md). Once you had done so, you can leave a comment on the PR stating that you had done the necessary testing.
 1. Please provide ways to test whatever you just modified on the bot in the [Test Cases section](https://github.com/CSSS/wall_e/blob/master/documentation/Working_on_Bot/Test_Cases.md) so that future PRs can be tested to ensure they dont break your code when merging to master
