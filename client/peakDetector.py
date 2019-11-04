#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  client/peakDetector.py
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
#      pin 16 (GPIO23) ------> MCP3008 R anode
#      pin 18 (GPIO24) ------> MCP3008 G anode
#      pin 22 (GPIO25) ------> MCP3008 B anode

import pyaudio, subprocess, spidev, time
from datetime import datetime
import numpy as np
import RPi.GPIO as GPIO
import solenoid

soundcardName = "USB PnP Sound Device" # see available cards list : aplay -l
alsaMixerControl = "Mic" # see available control list : amixer -c <cardIndex>
bitrate = pyaudio.paInt16
sampleRate = 44100
chunkSize = 512 # number of samples averaged
retrigger = 0.001 # in seconds, act as a debounce
minDuration, maxDuration = 0.005, 0.1 # in seconds, exceeding 100ms for maxDuration may break the solenoid
recoverTime = 0.3 # in seconds, when maxDuration has been reach, wait for this amount of time to avoid overheat
p, stream, spi = None, None, None
solenoidPin = solenoid.pin
isListening = True # allow the thread to quit
ALSAindex = None # index of the soundcard in the ALSA system to set input volumes
rgbPins = (16, 18, 22)
signalThreeshold = 200 # RGB will turn green when above this threeshold
redLedTimer = None # used to turn RGB on longer than the solenoid to stay visible
 
def listen() :
    # ~ global stream, p, spi, ALSAindex, meanPeaks
    global stream, p, spi, ALSAindex
    
    # Audio setup
    p=pyaudio.PyAudio()
    # Trying to find the soundcard ID
    OSSindex = None
    OSSindex, ALSAindex = findSoundcardIndexes()
    stream=p.open(format=bitrate,channels=1,rate=sampleRate,input_device_index=OSSindex, input=True, frames_per_buffer=chunkSize)
    
    # GPIO setup
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(solenoidPin, GPIO.OUT)
    GPIO.output(solenoidPin, GPIO.LOW)
    GPIO.setup(rgbPins, GPIO.OUT)
    GPIO.output(rgbPins, GPIO.LOW)
    GPIO.setwarnings(False)
    
    # SPI bus setup for MCP3008
    spi = spidev.SpiDev()
    spi.open(0,0)
    spi.max_speed_hz=1000000
    
    lastTrigger = datetime.now()
    recovering = False
    
    while isListening :
        try :
            
            threeshold = readPotentiometers() # update threeshold and gain
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
            updateRGBled(peak)
        except KeyboardInterrupt : return

# tries to close the stream without segfaulting
def stopListening() :
    global stream, p
    stream.stop_stream()
    stream.close()
    p.terminate()
    
# read SPI data from MCP3008 chip, return value as 0~1 float
def read3008Channel(channel):
    assert channel in range(7)
    adc = spi.xfer2([1,(8+channel)<<4,0])
    data = ((adc[1]&3) << 8) + adc[2]
    return data/1023

# set the alsa input volume according to the gain potentiometer and return the threeshold according to the second one
def readPotentiometers():
    ch0 = read3008Channel(0)
    thr = read3008Channel(1)*2 # magic number found by experimenting
    cmd = "amixer -c {} -q sset Mic {}%".format(ALSAindex, int(ch0*100))
    subprocess.call(cmd, shell=True)
    return thr

# make the RGB led goes green when there is signal present, red when the solenoid is activated and off when under threeshold
def updateRGBled(value) :
    global redLedTimer # we need to maintain the red led on for longer than the solenoid or it won't be visible at all
    if redLedTimer :
        if (datetime.now() - redLedTimer).total_seconds() > .2 : redLedTimer = None # so 200ms it is
        else : return
    if GPIO.input(solenoidPin) :
        redLedTimer = datetime.now()
        rgb = (True, False, False)
    elif value > signalThreeshold : rgb = (False, True, False)
    else : rgb = (False, False, False)
    for i in range(3) : GPIO.output(rgbPins[i], rgb[i])
    
# find the OSS index and the ALSA index associated with the soundcard used (by name)
def findSoundcardIndexes():
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    # get soundcard index for pyaudio through the OSS enumeration system
    for i in range(numdevices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            name = p.get_device_info_by_host_api_device_index(0, i).get('name')
            if name.count(soundcardName) : 
                OSSindex = i
                print("selected OSS card #%i : %s" %(OSSindex, name))
                break
    else : raise SystemError("Soundcard not found in OSS devices")
    # get soundcard index for alsa
    info = subprocess.check_output(["aplay", "-l"]).decode("utf-8")
    for line in info.splitlines() :
        if line.count(soundcardName) :
            ALSAindex = (line.split("card "))[1].split(": Device")[0]
            ALSAindex = int(ALSAindex)
            print("selected ALSA "+line)
            return OSSindex, ALSAindex
    raise SystemError(info + "\nSoundcard not found in ALSA devices")

if __name__ == '__main__':
    print("this file is made to be imported as a module, not executed")
    raise SystemError
