#!/bin/bash -e
set -e
create_box (){
  output="$@"
  greatestLength=0
  for i in "${output[@]}"
  do
    if [ $greatestLength -lt ${#i} ]; then
      greatestLength=${#i}
    fi
  done

  # section for printing top border
  echo; for i in $(seq $(($greatestLength + 8))); do echo -n "#"; done; echo
  echo -n "###"; for i in $(seq $(($greatestLength + 2))); do echo -n " "; done; echo "###"

  # sectiom for printing logs
  for i in "${output[@]}"
  do
    echo -tn "### "$i
    for i in $(seq $(($greatestLength - ${#i} +1 ))); do echo -n " "; done;
    echo "###"
  done
  
  # section for printing bottom border
  echo -n "###"; for i in $(seq $(($greatestLength + 2))); do echo -n " "; done;  echo "###"  
  for i in $(seq $(($greatestLength + 8))); do echo -n "#"; done;
  echo

}

user=`whoami`

option[0]="Adding jenkins repository key and repo source url"
create_box $output
wget -q -O - https://pkg.jenkins.io/debian/jenkins.io.key | sudo apt-key add -
sudo bash -c "echo 'deb https://pkg.jenkins.io/debian binary/' >> /etc/apt/sources.list"

option[0]="Adding docker repository key and repo source url"
create_box $output
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo apt-key fingerprint 0EBFCD88
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

option[0]="Updating apt-get with newly added sources"
create_box $output
sudo apt-get update

option[0]="Installing default-jre, redis-server, redis-tools, nginx"
option[1]="apt-transport-https, ca-certificates, curl"
option[2]="and software-properties-common"
create_box $output
sudo apt-get install -y default-jre
sudo apt-get install -y redis-server redis-tools
sudo apt-get install -y nginx
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common

option[0]="Installing docker"
create_box $output
sudo apt-get install -y docker-ce

option[0]="Creating docker group and adding "$user" to Docker group"
create_box $output
sudo groupadd docker
sudo usermod -aG docker $user


option[0]="Setting up SSL keys"
create_box $output
sudo openssl req -x509 -nodes -days 3650 -newkey rsa:2048 -keyout /etc/ssl/private/nginx-selfsigned.key -out /etc/ssl/certs/nginx-selfsigned.crt
sudo openssl dhparam -out /etc/ssl/certs/dhparam.pem 2048

sudo bash -c "echo 'ssl_certificate /etc/ssl/certs/nginx-selfsigned.crt;' >> /etc/nginx/snippets/self-signed.conf"
sudo bash -c "echo 'ssl_certificate_key /etc/ssl/private/nginx-selfsigned.key;' >> /etc/nginx/snippets/self-signed.conf"


sudo bash -c "echo 'ssl_protocols TLSv1 TLSv1.1 TLSv1.2;' >> /etc/nginx/snippets/ssl-params.conf"
sudo bash -c "echo 'ssl_prefer_server_ciphers on;' >> /etc/nginx/snippets/ssl-params.conf"
sudo bash -c "echo 'ssl_ciphers \"EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH\";' >> /etc/nginx/snippets/ssl-params.conf"
sudo bash -c "echo 'ssl_ecdh_curve secp384r1;' >> /etc/nginx/snippets/ssl-params.conf"
sudo bash -c "echo 'ssl_session_cache shared:SSL:10m;' >> /etc/nginx/snippets/ssl-params.conf"
sudo bash -c "echo 'ssl_session_tickets off;' >> /etc/nginx/snippets/ssl-params.conf"
sudo bash -c "echo 'ssl_dhparam /etc/ssl/certs/dhparam.pem;' >> /etc/nginx/snippets/ssl-params.conf"

option[0]="Installing jenkins and assigning user to jenkins group"
create_box $output
sudo apt-get install -y jenkins
sudo apt list jenkins
sudo usermod -aG docker jenkins
sudo service jenkins status
sudo service jenkins restart
sudo service jenkins status