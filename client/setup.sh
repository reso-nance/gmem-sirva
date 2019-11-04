#!/bin/bash
# This script install dependancies and configure the network for the raspberry pi clients
# usage : sudo bash setup.sh

thisClientHostname="gmemClientTest"

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
apt-get -y --fix-missing install python3-pip python3-dev  python3-rpi.gpio liblo-dev libasound2-dev \
libatlas-base-dev libportaudio0 libportaudio2 libportaudiocpp0 portaudio19-dev python3-spidev libjack0 jackd1 jack-tools||exit 1
echo "
installing pip packages :" # pip packages must be installed one by one to avoid dependencies issues
pip3 install Cython||exit 2
pip3 install pyliblo ||exit 2
pip3 install numpy ||exit 2
pip3 install pyaudio ||exit 2
pip3 install JACK-client ||exit 2
pip3 install soundfile ||exit 2


echo "
------------DONE installing dependencies------------
"
# compiling binaries from source
sudo -u pi chmod +x ./build
sudo -u pi ./build
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
#raspi-config nonint do_i2c 0 # doesn't work anymore on raspbian buster
echo "
dtparam=spi=on
">>/boot/config.txt

echo "
--------------- disabling bluetooth :---------------
"
echo "
dtoverlay=pi3-disable-bt
">>/boot/config.txt
systemctl disable hciuart.service
systemctl disable bluealsa.service
systemctl disable bluetooth.service

echo "
----------- disabling unneeded services :-----------
"
systemctl disable triggerhappy
systemctl disable dbus
echo "
----- setting CPU governor to performance mode -----
"
echo performance > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor


if [ "$(uname -r)" = "4.19.59-rt23-v7+" ]; then
    echo "already using realtime kernel"
  else
    echo "
----------installing realtime kernel :----------
"
    echo "  extracting pre-compiled kernel..."
    mkdir rtkernel
    tar xzf rt-kernel.tgz -C ./rtkernel
    echo "  copying files..."
    cd rtkernel
    cp *.dtb /boot/
    cd boot
    cp -rd * /boot/
    cd ../lib
    cp -dr * /lib/
    cd ../overlays
    cp -d * /boot/overlays
    cd ..
    cp -d bcm* /boot/
    cd ..
    rm -rf ./rtkernel
    echo "  adding kernel to /boot/config.txt..."
    echo "
kernel=${zImage name}
device_tree=bcm2710-rpi-3-b.dtb
">>/boot/config.txt
    echo "  patching cmdline.txt to ensure USB and ETH interrupts will not break..."
    # fixme
    #~ echo "dwc_otg.lpm_enable=0 dwc_otg.fiq_enable=0 dwc_otg.fiq_fsm_enable=0 dwc_otg.nak_holdoff=0 console=serial0,115200 console=tty1 root=PARTUUID=1b37641c-02 rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait
    #~ ">/boot/cmdline.txt
    
    echo "
----------finished installing realtime kernel :----------
"
fi
    echo "
--------------setting up script autolaunch:--------------
"
echo"
su pi -c '/usr/bin/python3 /home/pi/client/main.py'
">>/etc/rc.local

echo "
----------------------------------------------------
-------------- DONE, leaving setup.sh---------------
--------- this pi will reboot in 5 seconds----------
----------------------------------------------------
"
sleep 5
reboot
