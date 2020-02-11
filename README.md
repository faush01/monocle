**Setup Raspbian**

https://www.raspberrypi.org/downloads/raspbian/

set hostname, password, timezone

sudo nano /etc/hostname

sudo nano /etc/hosts

sudo passwd pi

sudo raspi-config

**Installing Flask**

sudo apt-get install git

sudo apt-get install python3-pip

sudo pip3 install flask

sudo pip3 install gevent

sudo pip3 install Flask-Sockets

**Running**

python3 flask_app.py <path to DB>
