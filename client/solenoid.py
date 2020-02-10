#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  client/solenoid.py
#  
#  Copyright 2019 Reso-nance Numérique <laurent@reso-nance.org>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#      -------------- Pinout --------------
#            RPI
#      pin 12 (GPIO18) ------> IRLZ34N gate
#      pin 19 (GPIO10) ------> MCP3008 MISO
#      pin 21 (GPIO09) ------> MCP3008 MOSI
#      pin 23 (GPIO11) ------> MCP3008 CLK
#      pin 24 (GPIO08) ------> MCP3008 CS
#  

import RPi.GPIO as GPIO
import time, subprocess
from threading import Thread
from datetime import datetime, timedelta

pin = 12
gpio = 18 # pin 12 = BCM GPIO 18
durationMin, durationMax = 10, 100 # in ms
retrigger = 0.1 # in ms, act as a debounce
recoverTime = 200 # in ms, when maxDuration has been reached, wait for this amount of time to avoid overheat

#GPIO setup
GPIO.setmode(GPIO.BOARD)
GPIO.setup(pin, GPIO.OUT)
GPIO.output(pin, GPIO.LOW)
# subprocess.Popen("raspi-gpio set %i op" % gpio, shell=True)

def setLOW() :
    # subprocess.Popen("raspi-gpio set %i dl" % gpio, shell=True)
    GPIO.output(pin, GPIO.LOW)


def setHIGH() : 
    # subprocess.Popen("raspi-gpio set %i dh" % gpio, shell=True)
    GPIO.output(pin, GPIO.HIGH)

def isON():
    raspiGpioResult = str(subprocess.run("raspi-gpio get %i" % gpio, shell=True, stdout=subprocess.PIPE))

    if raspiGpioResult.count("level=1") : return True
    elif raspiGpioResult.count("level=0") : return False
    else : print("ERROR : unable to read solenoid GPIO status : \n"+raspiGpioResult)

def setGPIOhigh(duration):
    print("solenoid on for %ims"%duration)
    startTime = datetime.now()
    sleepTime = timedelta(milliseconds = duration)
    setHIGH()
    while startTime+sleepTime > datetime.now(): pass
    setLOW()

def actuate(OSCaddress=None, OSCargs=None, tags=None, IPaddress=None, duration=None):
    if not duration : # called from the OSCserver
        if len(OSCargs) == 0 : duration=durationMax
        elif len(OSCargs) == 1 :
            try : duration = int(OSCargs[0])
            except ValueError : 
                try : duration = float(OSCargs[0])
                except : duration = durationMax
    duration = min(durationMax, max(durationMin, duration)) 
    Thread(target=setGPIOhigh, args=(duration,)).start()     

def noteOn(velocity) :
    duration = int(velocity/127*(durationMax-durationMin)+durationMin) # map 0~127 -> durationMin~durationMax
    actuate(duration=duration)
    
if __name__ == '__main__':
    print("this file is made to be imported as a module, not executed")
    raise SystemError
