**Setup Raspbian**

`https://www.raspberrypi.org/downloads/raspbian/`

**Update**

- `sudo apt-get update`
- `sudo apt full-upgrade`

**Set hostname, password, timezone**

- `sudo nano /etc/hostname`
- `sudo nano /etc/hosts`
- `sudo passwd pi`
- `sudo raspi-config`

**Installing Libs**

- `sudo apt-get install rpi.gpio`
- `sudo apt-get install git`
- `sudo apt-get install screen`
- `sudo apt-get install python3-pip`
- `sudo pip3 install flask`
- `sudo pip3 install gevent`
- `sudo pip3 install Flask-Sockets`


**Git Clone**

`git clone https://github.com/faush01/monocle.git`

**Running**

`python3 flask_app.py <path to DB>`
