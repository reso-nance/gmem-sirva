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
import json, os, datetime, random, time
import OSCserver, UI, midiFile
knownClientsFile = "knownClients.json"
knownClients = {}
disconnectedThread = True

# ~ class Client():
    # ~ def __init__(self, **kwargs):
        # ~ self.wavFiles = kwargs["wavFiles"] if "wavFiles" in kwargs else []
        # ~ self.name = kwargs["name"]
        # ~ self.IP = kwargs["IP"] if "IP" in kwargs else self.name + ".local"
        # ~ self.status = kwargs["status"] if "status" in kwargs else "inconnu"
        # ~ self.midiNote = kwargs["midiNote"] if "midiNote" in kwargs else 65
        # ~ self.volumes = kwargs["volumes"] if "volumes" in kwargs else {"microphone":50, "analogIN":50, "transducer":50, "analogOUT":50}
        # ~ self.updateVolumes()
        
    # ~ def setVolume(self, channel, volume):
        # ~ if channel in self.volumes.keys() :
            # ~ OSCserver.sendOSC(self.IP, "/volume", [channel, volume])
            # ~ self.volumes[channel] = volume
        # ~ else : raise Error("unable to set volume for channel '%s'" % channel)
        
    # ~ def updateVolume(self):
        # ~ OSCserver.sendOSC(self.IP, "/getVolumes")
    
    # ~ def toDict(self):
        # ~ return vars(self)

# refresh lastSeen, connected, status and IP of a device on heartbeat reception. If the device is unknown, ask for it's details
def processHeartbeat(command, args, tags, IPaddress):
    global knownClients
    hostname = args[0]
    sendersIP = IPaddress.url.split("//")[1].split(":")[0] # retrieve IP from an url like osc.udp://10.0.0.12:35147/
    if hostname in knownClients and "connected" not in knownClients[hostname].keys() : print("DEBUG no connected status : ",knownClients[hostname])
    if hostname not in knownClients : 
        print("received heartbeat from %s (%s), asked for details" % (hostname, sendersIP))
        OSCserver.sendOSC(sendersIP, "/getInfos")
    else : 
        if sendersIP != knownClients[hostname]["IP"] : knownClients[hostname]["IP"] = sendersIP
        knownClients[hostname]["status"] = "last "+getDate()
        knownClients[hostname]["lastSeen"] = time.time()
        if knownClients[hostname]["connected"] is False : 
            knownClients[hostname]["connected"] = True
            print(hostname+" reconnected")
        # print("received heartbeat from known client %s" % hostname)
    pass

# called when device send it's details. Add new device to the knownClients and fill in it's parameters
def processClientsInfos(command, args, tags, IPaddress):
    global knownClients
    print("got info from {} : {}".format(IPaddress.url, args))
    refreshUI = False
    hostname, midiNote, volMic, volAnalogIN, volTrans, volAnalogOUT = args
    IP = IPaddress.url.split("//")[1].split(":")[0] # retrieve IP from an url like osc.udp://10.0.0.12:35147/
    if hostname not in knownClients :
        print("adding new device %s to the known devices list")
        knownClients[hostname] = {}
        knownClients[hostname]["name"] = hostname
        knownClients[hostname]["fileList"] = []
        knownClients[hostname]["IP"] = IP
        knownClients[hostname]["midiNote"] = midiNote
        knownClients[hostname]["volumes"] = [volMic, volAnalogIN, volTrans, volAnalogOUT]
        knownClients[hostname]["status"] = "last "+getDate()
        knownClients[hostname]["connected"] = True
        knownClients[hostname]["lastSeen"] = time.time()
        OSCserver.sendOSC(IP, "/getFileList")
        refreshUI = True
        midiFile.updateNoteTranslator(knownClients)
    elif knownClients[hostname]["connected"] is False:
        knownClients[hostname]["connected"] = True
        knownClients[hostname]["lastSeen"] = time.time()
        if knownClients[hostname]["IP"] != IP : knownClients[hostname]["IP"] = IP
        knownClients[hostname]["fileList"] = []
        print("%s has reconnected" % hostname)
        OSCserver.sendOSC(IP, "/getFileList")
        refreshUI = True
    else : 
        knownClients[hostname]["lastSeen"] = time.time()
    
    if refreshUI : UI.refreshDeviceList()
    print (knownClients)

# called when a device sends it's wav file list, populates the fileList argument
def processFileList(command, args, tags, IPaddress):
    hostname = args[0]
    if hostname not in knownClients :
        OSCserver.sendOSC(IPaddress.url.split("//")[1].split(":")[0], "/getInfos") # retrieve IP from an url like osc.udp://10.0.0.12:35147/
        return
    else : 
        knownClients[hostname]["fileList"] = []
        for f in args[1:] : knownClients[hostname]["fileList"].append(f)
        print("got filelist from {} : {}".format(hostname, args[1:]))
        UI.refreshFileList(hostname, knownClients[hostname]["fileList"])

def readFromFile():
    global knownClients
    if os.path.isfile(knownClientsFile) :
        with open(knownClientsFile) as json_file : data = json.load(json_file)
        knownClients = data
        midiFile.updateNoteTranslator(knownClients)
    else :
        print("known clients file %s not found, creating a new one" % knownClientsFile)
        writeToFile()
    
def writeToFile():
    with open(knownClientsFile, 'w') as f : json.dump(knownClients, f)
    
def sendOSC(hostname, address, args=None):
    try : IPaddress = knownClients[hostname]["IP"]
    except KeyError :
        print("tried to send {} but client {} isn't in the knownClients anymore".format(address, hostname))
        print ("  known clients : {}".format(knownClients.keys()))
        return
    if args : OSCserver.sendOSC(IPaddress, address, args)
    else : OSCserver.sendOSC(IPaddress, address)
    
def changeParameter(hostname, paramName, value):
    global knownClients
    try : client = knownClients[hostname]
    except KeyError :
        print("tried to change parameter {} for client {} : client isn't in in the knownClients anymore".format(paramName, hostname))
        print ("  known clients : {}".format(knownClients.keys()))
        return
    if paramName in client :
        client[paramName] = value
        print("set {} {} to {}".format(hostname, paramName, value))
        if paramName == "midiNote" : midiFile.updateNoteTranslator(knownClients)
    else : print ("cannot update {} : unkown parameter".format(paramName))

# send the OSC message to change device hostname and remove it from the knownHost list
def changeHostname(oldHostname, newHostname):
    global knownClients
    sendOSC(oldHostname, "/changeHostname", newHostname)
    del knownClients[oldHostname]
    writeToFile()
    print("deleted client %s" % oldHostname, knownClients.keys())

# ~ def new(name, IP=None, status=None, midiNote=None, volumes = None,  ):
    # ~ if not IP : IP=name+".local"
    # ~ if not status : status = "en ligne depuis le " + getDate()
    # ~ if not midiNote : midiNote = random.randrange(12, 127)
    # ~ if not volumes : volumes=[0,0,0,0]
    
# return the actual date in human readable form
def getDate(date = None):
    if not date : date = datetime.datetime.now()
    return date.strftime("%d %b %Y %H:%M:%S")

# mark all known clients as disconnected and retrieve the last connected date via the lastSeen parameter (number of seconds since Epoch)
def init():
    global knownClients
    print("  marking all known clients as disconnected ")
    currentTime = time.time()
    for name in knownClients :
        print("initialising", knownClients[name])
        knownClients[name]["connected"] = False
        lastSeen = currentTime - knownClients[name]["lastSeen"]
        lastConnected = datetime.datetime.now() - datetime.timedelta(seconds=lastSeen)
        knownClients[name]["status"] = "déconnecté, vu pour la dernière fois le "+getDate(lastConnected)
    print("  asking for their ID")
    for name in knownClients : OSCserver.sendOSC(name+".local", "/getInfos")
    midiFile.updateNoteTranslator(knownClients)

# clear the list of known clients and remove the associated file
def forgetAll(clearCache=True):
    global knownClients
    if clearCache : os.remove(knownClientsFile)
    print("known clients file deleted")
    knownClients = {}
    readFromFile()
    
# reply to the sender with "/connectedClients hostname1 hostname2..." with the hostnames of connected clients
def whoIsThere(command, args, tags, IPaddress):
    connectedClients = [k for k in knownClients.keys() if knownClients[k]["connected"]]
    OSCserver.sendOSC(IPaddress.url.split("//")[1].split(":")[0], "/connectedClients", connectedClients)

# reply to the sender with "/connectedClients hostname1 hostname2..." with the hostnames of known clients, connected or not
def sendKnownClients(command, args, tags, IPaddress):
    OSCserver.sendOSC(IPaddress.url.split("//")[1].split(":")[0], "/knownClients", list(knownClients.keys()))

# mark devices which heartbeat have not been received for more than five seconds
def checkDisconnected():
    global knownClients
    while disconnectedThread :
        # ~ currentTime = datetime.datetime.now() # datetime would have been a better choice if only it was JSON-serialisable
        currentTime = time.time()
        for client in [c for c in knownClients if knownClients[c]["connected"]] :
            # ~ if (currentTime - client["lastSeen"]).total_seconds() > 2 : 
            if currentTime - knownClients[client]["lastSeen"] > 5 : 
                knownClients[client]["connected"] = False
                knownClients[client]["status"] = "déconnecté depuis le "+getDate()
                print("client %s is now marked as disconnected" % client)
        time.sleep(1)

if __name__ == '__main__':
    raise SystemError ("this clients file isn't made to be executed on it's own but to be imported as a module")
