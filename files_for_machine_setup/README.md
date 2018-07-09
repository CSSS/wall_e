# Part 1: Server Setup  
  
## Jenkins Setup on Docker
 1. Spin-up a linux server [This documentation was made with an Ubuntu 16.04.4 server]  
 2. run the following command  
```shell
./setup_environment_for_wall_e.sh
```
the above script was adapted from the commandline history gleamed from the commands used by the person who set up the server. If you encounter issues with the script, feel free to look at the command history instead at [command history.txt](command_history.txt)  
  
 3. docker container should end up being set up with  
          1. `Python 3.5.5`  
          2. `pip 10.0.1 from /usr/local/lib/python3.5/site-packages/pip (python 3.5)`  

## Nginx Set-up
 1. Compare the `/etc/nginx/sites-enabled/default` file on the machine vs the [default](default) file included in this repo to see if the server copy needs any changes.  
 1. Run `nginx -t` to test the configuration file.  
 1. If tests pass, run `sudo service nginx restart `  
  
## Redis setup
 1. Compare the `/etc/redis/redis.conf` file on the machine vs the [redis.conf](redis.conf) file included in this repo to see if the server copy needs any changes.  
 2. Misc. Commands that may be useful for this step  
         1. `sudo service redis-server restart`  
         2. `redis-cli --csv subscribe '__keyevent@0__:expired'`  
         3. `docker ps`  
         4. `docker stop wall-e-test`  
         5. `docker logs -f wall-e-test`  
         6. `docker start wall-e-test`  
         7. `docker rm wall-e-test `  