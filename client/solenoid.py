#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  client/solenoid.py
#  
#  Copyright 2019 Unknown <Sonnenblumen@localhost.localdomain>
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
#  
import RPi.GPIO as GPIO
import time
from threading import Thread
from datetime import datetime

pin = 12
durationMin, durationMax = 10, 100 # in ms
retrigger = 0.1 # in ms, act as a debounce
recoverTime = 200 # in ms, when maxDuration has been reach, wait for this amount of time to avoid overheat

GPIO.setmode(GPIO.BOARD)
GPIO.setup(pin, GPIO.OUT)
GPIO.output(pin, GPIO.LOW)

def setGPIOhigh(duration=durationMax) :
    try : duration = int(duration)
    except ValueError : 
        try : duration = float(duration)
        except : duration = durationMax
    duration = min(durationMax, max(durationMin, duration))
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(pin, GPIO.LOW)
    return

def noteOn(velocity) :
    duration = velocity/255*(durationMax-durationMin)+durationMin # map 0~255 -> durationMin~durationMax
    duration = duration /1000. # from ms to seconds
    Thread(target=setGPIOhigh, args=(duration,)).start() 
    
# ~ def startScheduler():
    # ~ beginPulse = datetime.now()
    # ~ endPulse = datetime.now()
    # ~ isHigh = False
    # ~ GPIO.setmode(GPIO.BOARD)
    # ~ GPIO.setup(pin, GPIO.OUT)
    # ~ GPIO.output(pin, GPIO.LOW)
    # ~ while True :
        # ~ if pulseDuration :
            # ~ pulseDuration = min(durationMax, max(durationMin, pulseDuration))
            
            # ~ endPulse = 
        # ~ if endPulse > 
    

if __name__ == '__main__':
    print("this file is made to be imported as a module, not executed")
    raise SystemError
