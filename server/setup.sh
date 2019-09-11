#!/bin/bash
# This script install dependancies and configure the network for the raspberry pi server
# usage : bash setup.sh

echo "
------------installing dependencies :------------
"
echo "
updating the system :"
sudo apt-get update||exit 1
sudo apt-get -y dist-upgrade||exit 1
echo "
installing .deb packages :"
sudo apt-get -y --fix-missing install python3-pip python3-dev liblo-dev libasound2-dev libjack-jackd2-dev portaudio19-dev ||exit 1
echo "
installing pip packages :"
pip3 install Cython||exit 2
pip3 install pyliblo ||exit 2
#~ pip3 install flask||exit 2
#~ pip3 install flask-socketio||exit 2
#~ pip3 install flask-uploads||exit 2
pip3 install python-rtmidi||exit 2
pip3 install mido||exit 2
#~ pip3 install eventlet||exit 2

echo "
------------DONE installing dependencies------------
"

chmod +x ./STAtoAP
sudo ./STAtoAP
