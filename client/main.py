#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  client/main.py
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

from threading import Thread
from time import sleep
import signal, subprocess
import OSCserver, peakDetector, audio

oscServerThread = None
peakDetectorThread = None
JACKconnectionThread = None

def exitCleanly():
    if oscServerThread : 
        print("closing the OSC server")
        OSCserver.runServer = False
        oscServerThread.join()
    if peakDetector :
        print("closing the peak detector")
        peakDetector.isListening = False
        peakDetector.stopListening()
    print("exiting jack client ...")
    audio.close()
    
    raise SystemExit

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, exitCleanly) # register this exitCleanly function to be called on sigterm
    print("starting the OSC server...")
    oscServerThread = Thread(target=OSCserver.listen)
    oscServerThread.start()
    print("starting the audio peak detector...")
    peakDetectorThread = Thread(target=peakDetector.listen)
    peakDetectorThread.start()
    print("starting the JACK connection thread...")
    JACKconnectionThread = Thread(target=audio.init)
    JACKconnectionThread.start()
    
    
    while True :
        try : sleep(1)
        except KeyboardInterrupt : exitCleanly()
