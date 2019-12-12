# the different CI files that are needed by wall_e


## used when doing local dev work

### Dockerfile.walle.mount

creates the image that is used when running wall-e locally when doing dev work

### docker-compose-mount-nodb.yml

runs the wall_e service locally without the database

### docker-compose-mount.yml

run the wall_e service locally with the database




## used by our jenkins

### Dockerfile.requirements

creates the [base] container that is uploaded to sfucsssorg/wall_e

### Dockerfile.test

creates the container used to test wall_e

### validate-formatting.sh

ensures that all plain text files are using Linux line endings

### Dockerfile.walle

creates image that is used to launch wall_e on the test guilds and the production guild

### Jenkinsfile

run whenever a push is done to wall_e repository

### Jenkinsfile_clean_branch

run whenever a branch is deleted on wall_e repository

### Jenkinsfile_clean_pr

run whenver a pr is closed on wall_e repository

### create-docker-image.sh

creates an updates wall_e docker image and uploads to sfucsssorg whenever a change is detected in the requirements file or Dockerfile.requirements

### docker-compose.yml

runs the wall_e service for test or production discord guilds

