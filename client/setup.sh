#!/bin/bash
# This script install dependancies and configure the network for the raspberry pi clients


if [[ $EUID -ne 0 ]]; then
   echo "Are you root enough ?" 
   exit 1
fi

echo "
------------installing dependencies :------------
"
echo "
updating the system :"
apt-get update||exit 1
apt-get -y dist-upgrade||exit 1
echo "
installing .deb packages :"
apt-get -y --fix-missing install python3-pip python3-dev  python3-rpi.gpio libasound2-dev libjack-jackd2-dev||exit 1
echo "
installing pip packages :"
pip3 install pyliblo ||exit 2

#~ pip3 install flask||exit 2
#~ pip3 install flask-socketio||exit 2
#~ pip3 install flask-uploads||exit 2
#~ pip3 install Cython||exit 2
#~ pip3 install eventlet||exit 2

echo "
------------DONE installing dependencies------------
"

echo '
network={
ssid="masterPi"
psk="bbqCvsN8"
proto=RSN
key_mgmt=WPA-PSK
pairwise=CCMP
auth_alg=OPEN
}
'>>/etc/wpa_supplicant/wpa_supplicant.conf
