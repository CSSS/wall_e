# the different CI files that are needed by wall_e


## used when doing local dev work

### docker-compose-mount-nodb.yml

runs the wall_e service locally without the database

### docker-compose-mount.yml

run the wall_e service locally with the database

### Dockerfile.walle.mount

creates the image that is used when running wall-e locally when doing dev work

### Dockerfile.walle.mount.nodb

creates the image that is used when running wall-e locally when doing dev work without the database
