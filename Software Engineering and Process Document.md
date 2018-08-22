# Software Engineering and Process Document

Created by Winfield Chen - wca988@sfu.ca

August 2018
Revision 1

## Table of Contents
 - [Architecture](#architecture)
   - [Overview](#overview)
   - [Docker](#Docker)
     - [Containers: A VM-Like Clean Running Environment For Wall-E]()
   - [Jenkins](#jenkins)
     - [Pipelines: An Automated Way to Run The Latest Version of Wall-E]()
 - [Process]()
   - [Making Changes to Wall-E]()
     - [Local Testing: Pitfalls and Necessity]()
   - [Proposing New Changes]()
 - [Procedure]()
   - [Jenkins Login]()
   - [Changing Jenkins Password]()
   - [Changing Bot Tokens]()
   - [Restarting Bot Using Jenkins]()
   - [Viewing Jenkins Output]()
 - [Appendix]()
   - [Required Environment Variables]()
   - [Local Testing Recommended Procedures]()
     - [Local Testing Outside of a Container]()
     - [Local Testing Inside of a Container]()
   - [The Role of Redis in the RemindMe Command]()
 - [Changelog]()

## Architecture

### Overview

![Image of Overview](overview.png) 

The Wall-E repository is synchronized with the Wall-E bot associated with the provided bot token. This is done using a continuous integration system known as Jenkins. The output of this automated process is the Wall-E bot inside of an isolated environment known as a Docker container, with some containers deployed with a testing token and containers from the repository master branch deployed with a production token.

### Docker

Docker is a computer program that performs operating-system-level virtualization, also known as containerization. Docker runs software packages called containers which are isolated bundles consisting only of a program and its dependencies such as tools, libraries, and configuration files. Containers are much like virtual machines except they are much more lightweight. Containers are created from images which specify the container’s filesystem and program run commands in a Dockerfile.

#### Containers: A VM-Like Clean Running Environment For Wall-E

Running Wall-E in a container brings with it several advantages. These advantages eliminate several categories of bugs stemming from poor package management and inconsistent developer environments. It is highly recommended that Wall-E be run in a Docker container at all times, including during local testing following the procedures as outlined in the appendix.

| Advantages of Running Wall-E in a Container | Disadvantages of Running Wall-E in a Container |
| ------------- |:-------------:|
|* Repeatable builds: no matter which computer is building the image, the same image is built. |* Harder to debug outside of an IDE: while IntelliJ IDEA can attach its debugger to programs inside of a running container it is much harder without an IDE. |
|* Known starting state: the container is always built from the base image, meaning packages are installed from scratch, avoiding versioning issues and package conflicts. |* Harder to access program output: output must be accessed using Docker’s log command or by an IDE. |
|* Isolation: Wall-E is isolated from the rest of the system as well as from other instances of itself. ||

### Jenkins

Jenkins is a software-development automation server which connects version control systems like Git to ready-to-run programs. Jenkins is the process component which commands the building of the Docker container and launches it with the correct production or test environment variables.

#### Pipelines: An Automated Way To Run The Latest Version Of Wall-E

Jenkins automates deployments of each push using a pipeline, a procedure of one or more steps known as stages which are found in a Jenkinsfile.

**Commonly-used stages in a Jenkins pipeline**

|||||
| ------------- |:-------------:| :-------------:| -----:|
| **Checkout**: the latest code is retrieved from version control | **Build**: the code is built into an application | **Test**: the application is tested (goes to testing) | **Deploy**: the application goes to production |


**Jenkins pipeline for Wall-E**

This process is triggered every push to the Wall-E repository

|||||
| ------------- |:-------------:| :-------------:| -----:|
| **Checkout**: the new code in the push is retrieved from Git | **Build**: the Docker image is built according to the Dockerfile | **Test**: a container of the image is run with the testing token and test variables | **Deploy**: if push is to master a container with the production token is run |

This pipeline is defined in the repository’s Jenkinsfile and is read in by Jenkins on each push. Github notifies Jenkins of new pushes using webhooks to the server.

## Process

### Making changes to Wall-E

|||||
| --- | --- | --- | --- |
| 1. Pick an issue from the repository. | 3. Start working on the issue **in the branch.**                                                              | 6. **Merge master** into your branch so you have others’ changes.            | 10. **Reviewer: test the changes on the test server** in addition to inspecting code before **approving.** |
| 2. **Make a branch** for that issue.  | 4. **Push frequently** so Jenkins can deploy your code to the test server so **bugs can be caught early on.** | 7. **After testing on the test server and locally** make a **pull request.** | 11. **Developer: merge and delete** the branch.                                                            |
|                                    | 5. **Test on the test server and locally** frequently for bugs.                                               | 8. Request a **review** from a reviewer.                                     |                                                                                                        |
|                                    |                                                                                                            | 9. **Continue Testing**                                                      |                                                                                                        |

#### Local Testing: Pitfalls and Necessity

Developers unfamiliar with continuous integration techniques may have a reliance on local testing which has the following disadvantages not present on the test server.
 * Package management and language versioning issues if not locally testing in a container
 * The need for a separate local test server         

However, local testing does make it possible to read application output in case of errors which makes it a necessity. The environment variables for this are in the appendix.

### Proposing New Changes

To propose a new change please make an issue on the repository.

## Procedure

### Jenkins Login

1. Go to [https://178.128.184.141/](https://178.128.184.141/)
1. Proceed through any browser security warnings.
   1. Advanced users may choose to install the **Computing Science Student Society Root CA** certificate authority into the browser.
1. Click **log in** at the top-right corner of the page.
1. Login with your provided credentials.

### Changing Jenkins Password

1. Click your name at the top-right corner of the page.
1. Click **Configure.**
1. Change your password and click **Save.**

### Changing Bot Token

1. From the Jenkins homepage (click the top-left logo) click on **Credentials**.
1. Click on **Wall-E Bot User Token**. If you would like to change the testing token, click on **Wall-E Bot User Token (Test)**.
1. Click on **Update**. Replace the contents of the Secret field with the new token. Click **Save**.

### Restarting Bot using Jenkins

1. From the Jenkins homepage (click the top-left logo) click on **wall-e**.
1. Click on **master**.
1. Click on **Build Now**.

### Viewing Jenkins Output

1. From the Jenkins homepage (click the top-left logo) click on **wall-e**.
1. Click on the desired branch.
1. Click on **Logs** of any stage in Stage View.
   1. Alternatively, click on a build number in the Build History.
   1. Or, click on a checkmark or X-mark from the repository.
   1. Or, click on a repository check’s **Details**.
1. Click on **Console Output**.

## Appendix

### Required Environment Variables

| Environment Variable | Local Testing | Test Server | Production Server |
| ------------- |:-------------:| -----:|
| Token         | Your server’s token. | Test server’s token. | Production server’s token. |
| ENVIRONMENT | You may choose any value other than TEST. | TEST | PRODUCTION |
| BRANCH     | Undefined. | Git branch’s name. | Undefined |

### Local Testing Recommended Procedures

#### Local Testing Outside Of A Container

 * Use of IntelliJ IDEA Ultimate Edition with Python plugin is recommended. A student license for the Ultimate Edition is available from Jetbrains with an email address from an educational institution.
 * Use the environment variable values for local testing specified above. They can be entered into the Edit Configurations page under the Run menu in the Python section’s Configuration tab.
 * Make sure the following items are installed.
   * Python 3.5.5
   * All packages in requirements.txt (IntelliJ will prompt to install these)
   * A Redis server on the local computer with key expiry event notifications enabled. This requires the line “notify-keyspace-events "Ex"” to be present in /etc/redis/redis.conf.
 * Run the bot from IntelliJ IDEA which will attach the Python debugger and display the output for you if you select the Debug option.

#### Local Testing Inside Of A Container

 * Use of IntelliJ IDEA Ultimate Edition with Python and Docker plugins is recommended.
 * Use the environment variable values for local testing specified above. They can be entered into the Edit Configurations page under the Run menu in the Docker Deployment section’s Container tab.
 * Since the container will need to access a Redis server running outside of it on the local machine, you will need to specify the Host Network Mode for Docker. On the aforementioned page select as the JSON file container_settings.json. This is the equivalent of adding the required “--net=host” flag to the command line.
 * Make sure a Redis server on the local computer with key expiry event notifications enabled is installed. This requires the line “notify-keyspace-events "Ex"” to be present in /etc/redis/redis.conf. 
 * Run the bot in a container from IntelliJ IDEA making sure to choose the Docker Deployment configuration.

### The Role Of Redis In The RemindMe Command

Redis is a key-value store database. Wall-E uses Redis to store and countdown pending reminders generated by the .remindme command. Below is a diagram of the system.

![Diagram of How redis is used with remindme command](remindme_diagram.png) 

| Advantages to Handling Reminders Using Redis | Disadvantages to Handling Reminders Using Redis                                                                                                                                                                        |
| ------------- | -----:|
| * Persistence: reminders would be lost on bot shutdown, crash, or update if reminders were handled in Wall-E. | * Additional external dependency: Wall-E requires Redis to function.                                                                                  |
| * Data-logic separation: better style.                                                                        | * Configuration required: Redis by default does not publish notifications; this must be enabled in the configuration file and is an extra setup step. |
| * Less development needed: by using a pre-made component the wheel need not be reinvented.                    | * Complicates structure: container must be able to talk to Redis on the localhost which is an additional complexity.                                  |
| * Available for future features: Redis can also be used for future stateful features like XP tracking.        |                                                                                                                                                       |

Ultimately, using a database like Redis which has features so closely related to the reminder functionality required is advantageous.

## Changelog

| August 2018 | Revision 1 | Initial Version