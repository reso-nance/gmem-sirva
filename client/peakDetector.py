#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  client/peakDetector.py
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
import pyaudio, time
from datetime import datetime
import numpy as np
import RPi.GPIO as GPIO
import solenoid

bitrate = pyaudio.paInt16
sampleRate = 44100
chunkSize = 512
threeshold = 1
retrigger = 0.001 # in seconds, act as a debounce
minDuration, maxDuration = 0.005, 0.1 # in seconds, exceeding 100ms for maxDuration may break the solenoid
recoverTime = 0.3 # in seconds, when maxDuration has been reach, wait for this amount of time to avoid overheat
p=pyaudio.PyAudio()
stream=None
solenoidPin = solenoid.pin

def listen() :
    global stream
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(solenoidPin, GPIO.OUT)
    GPIO.output(solenoidPin, GPIO.LOW)
    stream=p.open(format=bitrate,channels=1,rate=sampleRate,input=True, frames_per_buffer=chunkSize)
    lastTrigger = datetime.now()
    while True :
        try :
            readPotentiometers()
            data = np.fromstring(stream.read(chunkSize, exception_on_overflow = False),dtype=np.int16)
            peak=np.average(np.abs(data))*2
            if peak/chunkSize >= threeshold :
                if not GPIO.input(solenoidPin) and (datetime.now() - lastTrigger).total_seconds() >= retrigger :
                    lastTrigger = datetime.now()
                    GPIO.output(solenoidPin, GPIO.HIGH)
                if GPIO.input(solenoidPin) and (datetime.now() - lastTrigger).total_seconds() >= maxDuration :
                    GPIO.output(solenoidPin, GPIO.LOW)
                    time.sleep(recoverTime)
            else : GPIO.output(solenoidPin, GPIO.LOW)
            # ~ print("threeshold = %02f" % (peak/chunkSize))
        except KeyboardInterrupt : return

def stopListening() :
    stream.stop_stream()
    stream.close()
    p.terminate()
    
def readPotentiometers():
    pass


if __name__ == '__main__':
    print("this file is made to be imported as a module, not executed")
    raise SystemError
