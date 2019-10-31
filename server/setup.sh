#!/bin/bash
# This script install dependancies and configure the network for the raspberry pi server
# usage : bash setup.sh

thisScriptDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

echo "
------------installing dependencies :------------
"
echo "
updating the system :"
sudo apt-get update||exit 1
sudo apt-get -y dist-upgrade||exit 1
echo "
installing .deb packages :"
sudo apt-get -y --fix-missing install python3-pip python3-dev liblo-dev libasound2-dev libjack-jackd2-dev portaudio19-dev unclutter sshpass ||exit 1
echo "
installing pip packages :"
pip3 install Cython||exit 2
pip3 install pyliblo ||exit 2
pip3 install flask||exit 2
pip3 install flask-socketio||exit 2
pip3 install flask-uploads||exit 2
pip3 install python-rtmidi||exit 2
pip3 install mido||exit 2
pip3 install eventlet||exit 2

echo "
------------DONE installing dependencies------------
"
echo "
---------- configuring browser auto-start: ---------

"
sudo touch /etc/xdg/lxsession/LXDE-pi/autostart
echo "
# Auto run the browser
@xset s off
@xset -dpms
@xset s noblank
@unclutter -idle 0
@python3 /home/pi/server/main.py > /home/pi/server/server\`date +%d%m%y%H%M\`.log
@chromium-browser --kiosk $thisScriptDir/templates/loading.html
"| sudo tee -a /etc/xdg/lxsession/LXDE-pi/autostart > /dev/null # for raspbian buster
#~ "| sudo tee -a /.config/lxsession/LXDE-pi/autostart > /dev/null # for raspbian stretch
echo "
--------------- disabling sleep mode ---------------
"
echo "
xserver-command=X -s 0 dpms
"| sudo tee -a /etc/lightdm/lightdm.conf > /dev/null

echo "
--------- setting up the wifi country as FR---------"
sudo raspi-config nonint do_wifi_country FR

chmod +x ./STAtoAP
sudo ./STAtoAP
