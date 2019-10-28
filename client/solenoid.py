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
import time, spidev
from threading import Thread
from datetime import datetime

pin = 12
durationMin, durationMax = 10, 100 # in ms
retrigger = 0.1 # in ms, act as a debounce
recoverTime = 200 # in ms, when maxDuration has been reached, wait for this amount of time to avoid overheat

# GPIO setup
GPIO.setmode(GPIO.BOARD)
GPIO.setup(pin, GPIO.OUT)
GPIO.output(pin, GPIO.LOW)

def setGPIOhigh(duration) :
    duration = min(durationMax, max(durationMin, duration))
    print("on", duration, "ms")
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(pin, GPIO.LOW)
    return
    
def actuate(OSCaddress, OSCargs):
    if len(OSCargs) == 0 : duration=durationMax
    elif len(OSCargs) == 1 :
        try : duration = int(OSCargs[0])
        except ValueError : 
            try : duration = float(OSCargs[0])
            except : duration = durationMax
    Thread(target=setGPIOhigh, args=(duration,)).start() 
    

def noteOn(velocity) :
    duration = velocity/255*(durationMax-durationMin)+durationMin # map 0~255 -> durationMin~durationMax
    duration = duration /1000. # from ms to seconds
    actuate(duration)
    
if __name__ == '__main__':
    print("this file is made to be imported as a module, not executed")
    raise SystemError
