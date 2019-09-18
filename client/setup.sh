#!/bin/bash
# This script install dependancies and configure the network for the raspberry pi clients
# usage : sudo bash setup.sh

thisClientHostname=gmemClientTest

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
apt-get -y --fix-missing install python3-pip python3-dev  python3-rpi.gpio liblo-dev libasound2-dev libjack-jackd2-dev libatlas-base-dev libportaudio0 libportaudio2 libportaudiocpp0 portaudio19-dev spidev||exit 1
echo "
installing pip packages :"
pip3 install Cython||exit 2
pip3 install pyliblo ||exit 2
pip3 install numpy ||exit 2
pip3 install pyaudio ||exit 2

#~ pip3 install flask||exit 2
#~ pip3 install flask-socketio||exit 2
#~ pip3 install flask-uploads||exit 2
#~ pip3 install Cython||exit 2
#~ pip3 install eventlet||exit 2

echo "
------------DONE installing dependencies------------
"

echo "
----------------configuring network :----------------
"
echo "  adding masterPi network to wifi access points..."
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
echo "  setting hostname to $thisClientHostname..."
raspi-config nonint do_hostname "$thisClientHostname"
echo "
------------------ enabling SPI :-------------------
"
raspi-config nonint do_i2c 0
echo "
-------------- DONE, leaving setup.sh---------------
----------------------------------------------------
"
