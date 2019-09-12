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
import pyaudio
from datetime import datetime
import numpy as np
import RPi.GPIO as GPIO
import solenoid

bitrate = pyaudio.paInt16
sampleRate = 44100
chunkSize = 512 # number of samples averaged
threeshold = 1
retrigger = 0.001 # in seconds, act as a debounce
minDuration, maxDuration = 0.005, 0.1 # in seconds, exceeding 100ms for maxDuration may break the solenoid
recoverTime = 0.3 # in seconds, when maxDuration has been reach, wait for this amount of time to avoid overheat
p, stream = None, None
solenoidPin = solenoid.pin
 
def listen() :
    global stream, p
    
    # Audio setup
    p=pyaudio.PyAudio()
    stream=p.open(format=bitrate,channels=1,rate=sampleRate,input=True, frames_per_buffer=chunkSize)
    
    # GPIO setup
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(solenoidPin, GPIO.OUT)
    GPIO.output(solenoidPin, GPIO.LOW)
    
    # SPI bus setup
    spi = spidev.SpiDev()
    spi.open(0,0)
    spi.max_speed_hz=1000000
    
    lastTrigger = datetime.now()
    recovering = False
    
    while True :
        try :
            readPotentiometers() # update threeshold and gain
            # read a chunk inside a numpy array and average it's values
            data = np.fromstring(stream.read(chunkSize, exception_on_overflow = False),dtype=np.int16)
            peak=np.average(np.abs(data))*2
            currentTime = datetime.now()
            if peak/chunkSize >= threeshold :
                # if the solenoid is inactive, activate it
                if not GPIO.input(solenoidPin) and (currentTime - lastTrigger).total_seconds() >= retrigger and not recovering :
                    lastTrigger = currentTime
                    GPIO.output(solenoidPin, GPIO.HIGH)
                # if it has been fired for too long, shut it down to avoid overheating
                if GPIO.input(solenoidPin) and (currentTime - lastTrigger).total_seconds() >= maxDuration :
                    GPIO.output(solenoidPin, GPIO.LOW)
                    recovering = currentTime
            # when the audio data get under the threeshold and the solenoid is out, power it down
            elif GPIO.input(solenoidPin) : GPIO.output(solenoidPin, GPIO.LOW)
            # reset the recovery period
            elif recovering and (currentTime - recovering).total_seconds() > recoverTime : recovering = False
            # ~ print("threeshold = %02f" % (peak/chunkSize))
        except KeyboardInterrupt : return

def stopListening() :
    stream.stop_stream()
    stream.close()
    p.terminate()
    
# Function to read SPI data from MCP3008 chip
def read3008Channel(channel):
    assert channel in range(7)
    adc = spi.xfer2([1,(8+channel)<<4,0])
    data = ((adc[1]&3) << 8) + adc[2]
    return data/1024
    
def readPotentiometers():
    ch0 = read3008Channel(0)
    ch1 = read3008Channel(1)
    return ch0, ch1

if __name__ == '__main__':
    print("this file is made to be imported as a module, not executed")
    raise SystemError
