#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  server/clients.py
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

# ~ from threading import Thread
import json, os
import OSCserver
knownClientsFile = "knownClients.json"
knownClients = {}

class Client():
    def __init__(self, **kwargs):
        self.wavFiles = kwargs["wavFiles"] if "wavFiles" in kwargs else []
        self.name = kwargs["name"]
        self.IP = kwargs["IP"] if "IP" in kwargs else self.name + ".local"
        self.status = kwargs["status"] if "status" in kwargs else "inconnu"
        self.midiNote = kwargs["midiNote"] if "midiNote" in kwargs else 65
        self.volumes = kwargs["volumes"] if "volumes" in kwargs else {"microphone":50, "analogIN":50, "transducer":50, "analogOUT":50}
        self.updateVolumes()
        
    def setVolume(self, channel, volume):
        if channel in self.volumes.keys() :
            OSCserver.sendOSC(self.IP, "/volume", [channel, volume])
            self.volumes[channel] = volume
        else : raise Error("unable to set volume for channel '%s'" % channel)
        
    def updateVolume(self):
        OSCserver.sendOSC(self.IP, "/getVolumes")
    
    def toDict(self):
        return vars(self)

def processHeartbeat(command, args, tags, IPaddress):
    sendersIP = IPaddress.url.split("//")[1].split(":")[0] # retrieve IP from an url like osc.udp://10.0.0.12:35147/
    if args[0] not in knownClients : 
        print("received heartbeat from %s (%s), asked for details" % (args[0], sendersIP))
        OSCserver.sendOSC(sendersIP, "/getInfos")
    pass

def processClientsInfos(command, args, tags, IPaddress):
    global knownClients
    hostname, IP, midiNote, volMic, volAnalogIN, volTrans, volAnalogOUT = args
    if hostname not in knownClients :
        print("adding new device %s to the known devices list")
        knownClients[hostname] = {}
        knownClients[hostname]["fileList"] = []
        OSCserver.sendOSC(IP, "/getFileList")
    knownClients[hostname]["IP"] = IP
    knownClients[hostname]["midiNote"] = midiNote
    knownClients[hostname]["volumes"] = [volMic, volAnalogIN, volTrans, volAnalogOUT]

def processFileList(command, args, tags, IPaddress):
    hostname = arg[0]
    if hostname not in knownClients :
        OSCserver.sendOSC(IPaddress.url.split("//")[1].split(":")[0], "/getInfos") # retrieve IP from an url like osc.udp://10.0.0.12:35147/
        return
    else : 
        knownClients[hostname]["fileList"] = []
        for f in args[1:] : knownClients[hostname]["fileList"].append(f)

if __name__ == '__main__':
    raise SystemError ("this clients file isn't made to be executed on it's own but to be imported as a module")

def readFromFile():
    global knownClients
    if os.path.isfile(knownClientsFile) :
        with open(knownClientsFile) as json_file : data = json.load(json_file)
        knownClients = data
    else :
        print("known clients file %s not found, creating a new one" % knownClientsFile)
        writeToFile()
    
def writeToFile():
    with open(knownClientsFile, 'w') as f : json.dump(knownClients, f)
    
def sendList():
    pass

def addClient(clientDict):
    pass
