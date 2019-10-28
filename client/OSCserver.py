#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  client/OSCserver.py
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
#  
import liblo, socket, os, glob
import solenoid, audio

listenPort = 9000
sendPort = 8000
server = None
runServer = True
masterPiIP = ("10.0.0.1", 8000)
myHostname = socket.gethostname()
myIP = getLocalIP()
hearbeat = True

def unknownOSC(path, args, types, src):
    print("got unknown message '%s' from '%s'" % (path, src.url))
    for a, t in zip(args, types):
        print ("  argument of type '%s': %s" % (t, a))

def listen():
    global server
    try:
        server = liblo.Server(listenPort)
        print("listening to incoming OSC on port %i" % listenPort)
    except liblo.ServerError as e:
        print(e)
        raise SystemError
        
    server.add_method("/solenoid", None, solenoid.actuate) # ex1 : /solenoid | ex2 : /solenoid 50 (pulse duration in ms)
    server.add_method("/play", None, audio.playFile) # ex : /readAudio myfile.wav [transducer] : if no output is named, defaults to transducer
    server.add_method("/route", None, audio.route) # ex : /route analogIN analogOUT
    server.add_method("/mute", None, audio.mute) # ex : /mute analogOUT
    server.add_method("/unmute", None, audio.mute) # ex : /unmute analogOUT
    server.add_method("/toggle", None, audio.mute) # ex : /toggle analogOUT
    server.add_method("/volume", None, audio.setVolume) # ex : /volume analogOUT 96
    server.add_method("/shutdown", None, shutdown) # ex : /volume analogOUT 96
    server.add_method("/getFileList", None, sendFileList) # ex : /volume analogOUT 96
    server.add_method(None, None, unknownOSC)
    
    while runServer : 
        server.recv(100)
    print("  OSC server has closed")

def sendHeartbeat():
    while heartbeat : 
        liblo.send(masterPiIP, "/hearbeat", [myHostname])
        time.sleep(1)

def sendOSC(IPaddress, command, args):
    print("sending OSC {} {} to {}".format(command, args, IPaddress))
    liblo.send((IPaddress, sendPort), command, args)

def shutdown(IPaddress, command, args) :
    print("asked for shutdown via OSC from {}".format(IPaddress))
    os.system("sudo shutdown now &")
    raise SystemExit

def sendFileList(command, args, tags, IPaddress):
    fileList = [myHostname] + glob.glob("wav/*.wav")
    OSCserver.sendOSC(masterPiIP, "/fileList", fileList)

def sendID():
    
    liblo.send(masterPiIP, "/ID", [myHostname, myIP, midinote, vol, vol, vol, vol])
     

def getLocalIP(): # a bit hacky but still does the job
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("10.0.0.1", 80)) # this IP doesn't need to be reacheable
    localIP = s.getsockname()[0]
    s.close()
    return localIP

if __name__ == '__main__':
    print("this file is made to be imported as a module, not executed")
    raise SystemError
