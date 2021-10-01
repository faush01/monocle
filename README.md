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

**Only needed if running flask web app (Optional)**

- `sudo apt-get install python3-pip`
- `sudo pip3 install flask`
- `sudo pip3 install gevent`
- `sudo pip3 install Flask-Sockets`

**Git Clone**

`git clone https://github.com/faush01/monocle.git`

**Running Logger At Startup**

`sudo crontab -e`

Add lines

```
@reboot stdbuf -o0 python3 -u /home/pi/monocle/scripts/logger.py run > /home/pi/monocle/logger.log 2>&1 & disown
0 2 * * * /sbin/shutdown -r now
```

**Running Flask Web App (Optional)**

`python3 flask_app.py <path to DB>`

**Headless Wifi on the Pi**

wpa_supplicant.conf
```
country=AU
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="NETWORK-NAME"
    psk="NETWORK-PASSWORD"
}
```
Enable SSH
Create empty file /Volumes/boot/ssh

**DHT22 Temperature and Relative Humidity Sensor**

- `sudo apt-get install python3-dev python3-pip`
- `sudo python3 -m pip install --upgrade pip setuptools wheel`
- `sudo pip3 install Adafruit_DHT`

