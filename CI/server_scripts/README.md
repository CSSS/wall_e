# the different CI files that are needed by wall_e

### create-docker-image.sh

creates an updates wall_e docker image and uploads to sfucsssorg whenever a change is detected in the requirements file or Dockerfile.requirements

### docker-compose.yml

runs the wall_e service for test or production discord guilds

### Dockerfile.requirements

creates the [base] container that is uploaded to sfucsssorg/wall_e

### Dockerfile.walle

creates image that is used to launch wall_e on the test guilds and the production guild

### Jenkinsfile

run whenever a push is done to wall_e repository

### Jenkinsfile_clean_branch

run whenever a branch is deleted on wall_e repository

### Jenkinsfile_clean_pr

run whenver a pr is closed on wall_e repository

### validate-formatting.sh

ensures that all plain text files are using Linux line endings
