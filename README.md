# **Udacity Linux Project**

# IP and URL address

IP address is `3.83.75.217`
URL is `http://3.83.75.217.xip.io/catalog`

## Create a new user named grader, give him root privileges and ssh key access
**Create user grader**
```sh
sudo adduser grader
```
**Give grader root privileges (sudo)**
```sh
sudo touch /etc/sudoers.d/grader
```
Add the following to the grader file
```sh
grader ALL=(ALL:ALL) ALL
```
## Set ssh login using keys
Generate keys on local machine using ssh-keygen and save them at ~/.ssh dir on local machine
On your server at /home/grader directory create .ssh dir and authorized_keys file:
```sh
su - grader
mkdir .ssh
touch .ssh/authorized_keys
nano .ssh/authorized_keys
```
Copy the public key (the .pub file) generated on your local machine to this authorized_keys file.
Change permissions to the dir and file:
```sh
chmod 700 .ssh
chmod 644 .ssh/authorized_keys
```
Reload SSH 
```sh
service ssh restart
```
Now you can use ssh to login with the new user (grader) just created
```sh
ssh grader@3.83.75.217 -p 2200 -i ~/.ssh/grader
```
Note: if you are enable to login then you may need to change the permissions in your server to the .ssh dir to 755 (sudo chmod 755 chmod) and change owner to grader (sudo chown grader .ssh)

## Change the SSH port from 22 to 2200
```sh
sudo nano /etc/ssh/sshd_config
```
Note: you may not want to delete port 22 and just add port 2200 until you verify you can connect through port 2200

Reload ssh
```sh
sudo service ssh restart
```
## Configure the Uncomplicated Firewall (UFW)
Configure the Uncomplicated Firewall (UFW) to only allow incoming connections for SSH (port 2200), HTTP (port 80), and NTP (port 123)
```sh
sudo ufw allow 2200/tcp
sudo ufw allow 80/tcp
sudo ufw allow 123/udp
sudo ufw enable
```
**Configure the local timezone to UTC**
```sh
sudo dpkg-reconfigure tzdata
```

# Software installation and updates
**Update currently installed packages**
```sh
sudo apt-get update
sudo apt-get upgrade
```
**Install Apache**
```sh
sudo apt-get install apache2
```
**Install mod_wsgi**
```sh
sudo apt-get install python-setuptools libapache2-mod-wsgi
```
**Restart Apache**
```sh
sudo service apache2 restart
```
**Install PostgreSQL**
```sh
sudo apt-get install postgresql
```
**Login as user "postgres"**
```sh
sudo su - postgres
```
**Get into postgreSQL shell**
```sh
psql
```
**Create a new database named catalog and create a new user named catalog in postgreSQL shell**
```sh
CREATE DATABASE catalog;
CREATE USER catalog;
```
**Set a password for user catalog**
```sh
ALTER ROLE catalog WITH PASSWORD 'password';
```
**Give user "catalog" permission to "catalog" application database**
```sh
GRANT ALL PRIVILEGES ON DATABASE catalog TO catalog;
```
**Quit postgreSQL and exit from user "postgres"**
```sh
\q
exit
```
## Install git, clone and setup your Catalog App project
**Install git**
```sh
sudo apt-get install git
```
**Setup your app directory**
```sh
cd /var/www
mkdir FlaskApp
cd FlaskApp
```
**Clone your catalog project**
```sh
git clone https://github.com/jsnavarr/iCatalogIMG
```
**Rename the project to FlaskApp**
```sh
sudo mv .iCatalogIMG ./FlaskApp
```
**Move to inner FlaskApp dir and rename main .py file**
```sh
cd FlaskApp
sudo mv catalog.py __init__.py
```
**Edit the .py files to use postgresql instead of sqlite**
Change 
```sh
engine = create_engine('sqlite:///catalog.db')
```
to 
```sh
engine = create_engine('postgresql://catalog:password@localhost/catalog')
```
**Install pip**
```sh
sudo apt-get install python-pip
```
**Install psycopg2**
```sh
sudo apt-get -qqy install postgresql python-psycopg2
```
**Create database schema**
```sh
sudo python database_setup.py
```

## Configure and Enable a New Virtual Host
**Create FlaskApp.conf file at /etc/apache2/sites-available/ and edit it**
```sh
sudo touch /etc/apache2/sites-available/FlaskApp.conf
sudo nano /etc/apache2/sites-available/FlaskApp.conf
```
**Add the following lines of code to the file to configure the virtual host**
```sh
<VirtualHost *:80>
	ServerName ec2-18-216-71-137.compute-1.amazonaws.com
	ServerAdmin danielpaladar@gmail.com
	WSGIScriptAlias / /var/www/FlaskApp/flaskapp.wsgi
	<Directory /var/www/FlaskApp/FlaskApp/>
		Order allow,deny
		Allow from all
	</Directory>
	Alias /static /var/www/FlaskApp/FlaskApp/static
	<Directory /var/www/FlaskApp/FlaskApp/static/>
		Order allow,deny
		Allow from all
	</Directory>
	ErrorLog ${APACHE_LOG_DIR}/error.log
	LogLevel warn
	CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
Enable the virtual host with the following command: sudo a2ensite FlaskApp
```
**Create the .wsgi file at /var/www/FlaskApp dir and edit it**
```sh
sudo touch /var/www/FlaskApp/flaskapp.wsgi
sudo nano /var/www/FlaskApp/flaskapp.wsgi
```
**Add the following lines of code to the flaskapp.wsgi file:**
```sh
#!/usr/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/FlaskApp/")

from FlaskApp import app as application
application.secret_key = 'Add your secret key'
```
**Restart Apache**
```sh
sudo service apache2 restart
```

