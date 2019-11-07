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
import liblo, socket, os, glob, random, time
import solenoid, audio

listenPort = 9000
sendPort = 8000
server = None
runServer = True
masterPiIP = ("10.0.0.1", 8000)
myHostname = socket.gethostname()
myIP = None
heartbeat = True
midinote = None

def unknownOSC(path, args, types, src):
    print("got unknown message '%s' from '%s'" % (path, src.url))
    for a, t in zip(args, types):
        print ("  argument of type '%s': %s" % (t, a))

def listen():
    global server
    readMidiNote()
    if not os.path.isdir("wav") : os.makedirs("wav")
    myIP = getLocalIP()
    try:
        server = liblo.Server(listenPort)
        print("listening to incoming OSC on port %i" % listenPort)
    except liblo.ServerError as e:
        print(e)
        raise SystemError
        
    server.add_method("/solenoid", None, solenoid.actuate) # ex1 : /solenoid | ex2 : /solenoid 50 (pulse duration in ms)
    server.add_method("/play", None, audio.playFile) # ex : /readAudio myfile.wav [transducer] : if no output is named, defaults to transducer
    server.add_method("/stop", None, audio.stop) # ex : /stop
    server.add_method("/route", None, audio.route) # ex : /route analogIN analogOUT
    server.add_method("/disconnect", None, audio.disconnect) # ex : /unroute analogIN
    server.add_method("/mute", None, audio.mute) # ex : /mute analogOUT
    server.add_method("/unmute", None, audio.mute) # ex : /unmute analogOUT
    server.add_method("/toggle", None, audio.mute) # ex : /toggle analogOUT
    server.add_method("/volume", None, audio.setVolume) # ex : /volume analogOUT 96
    server.add_method("/delete", None, deleteAudioFile) # ex : /volume analogOUT 96
    server.add_method("/shutdown", None, shutdown) # ex : /volume analogOUT 96
    server.add_method("/getFileList", None, sendFileList) # ex : /volume analogOUT 96
    server.add_method("/getInfos", None, sendID) # ex : /volume analogOUT 96
    server.add_method("/changeHostname", None, changeHostname) # ex : /volume analogOUT 96
    server.add_method(None, None, unknownOSC)
    
    while runServer : 
        server.recv(100)
    print("  OSC server has closed")

def sendHeartbeat():
    while heartbeat : 
        # ~ liblo.send(masterPiIP, "/heartbeat", myHostname)
        sendOSCtoServer("/heartbeat", [myHostname])
        # ~ print("sent heartbeat to {}".format(masterPiIP))
        time.sleep(1)

def sendOSC(IPaddress, command, args=None,):
    print("sending OSC {} {} to {}".format(command, args, IPaddress))
    if args : liblo.send((IPaddress, sendPort), command, *args)
    else : liblo.send((IPaddress, sendPort), command)

def sendOSCtoServer(command, args=None):
    if args : liblo.send(masterPiIP, command, *args)
    else : liblo.send(masterPiIP, command)

def shutdown(command, args, tags, IPaddress) :
    print("asked for shutdown via OSC from {}".format(IPaddress))
    os.system("sudo shutdown now &")
    raise SystemExit

def changeHostname(command, args, tags, IPaddress):
    global myHostname
    hostname = args[0]
    print("asked to change hostname from %s to %s" % (myHostname, hostname))
    os.system("sudo raspi-config nonint do_hostname \"%s\"" % hostname)
    errCode = 1
    while errCode != 0 : errCode = os.system('sudo hostnamectl set-hostname "%s"'%hostname) # workaround "temporary failure in name resolution"
    os.system("sudo  systemctl restart avahi-daemon") # needed to avoid a reboot
    time.sleep(3)
    myHostname = socket.gethostname()
    sendID()

def sendFileList(command, args, tags, IPaddress):
    fileList = [myHostname] + [f.replace("wav/", "") for f in glob.glob("wav/*")]
    # ~ liblo.send(masterPiIP, "/filesList", *fileList)
    sendOSCtoServer("/filesList", fileList)
    print("sent file list {}".format(fileList))

def sendID(command=None, args=None, tags=None, IPaddress=None):
    args = [myHostname, midinote]
    args += audio.getVolumes()
    sendOSCtoServer("/myID", args)
    # ~ liblo.send(masterPiIP, "/myID", *args)
     
def refreshVolumes():
    sendOSCtoServer("/myVolumes", audio.getVolumes())

def deleteAudioFile(OSCaddress, args, tags, IPaddress):
    audio.delete(OSCaddress, args, tags, IPaddress)
    sendFileList(OSCaddress, args, tags, IPaddress)

def getLocalIP(): # a bit hacky but still does the job
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("10.0.0.1", 80)) # this IP doesn't need to be reacheable
    localIP = s.getsockname()[0]
    s.close()
    return localIP

def readMidiNote():
    global midinote
    textFile = [f.replace(" ","") for f in glob.glob("*.txt") if "midinote" in f]
    if len(textFile) > 0: 
        midiNote = textFile[0].split("midinote")[1].split(".")[0]
        try :
            midiNote = int(midiNote)
            if midiNote in range(12, 128):
                print("read midiNote from file, set to %i" % midiNote)
                midinote = midiNote
                return
            else : print("midinote not in range 12~127 : %i" % midiNote)
        except ValueError :
            print("invalid midinote file : "+textFile[0])
    midinote = random.randrange(12, 128)
    print("set midiNote at random : %i" % midinote)
    writeMidiNote()

def writeMidiNote():
    textFile = [f for f in glob.glob("*.txt") if "midinote" in f]
    if len(textFile) > 0 :
        for f in textFile : 
            print("deleting midinote file : %s" %f)
            os.remove(f)
    filename = "midinote" +str(midinote) + ".txt"
    with open(filename, "w+") as f : f.write("le numéro de la note midi de cet appareil doit se trouver dans le nom de fichier, précédé du mot 'midinote'\nEx: 'midinote64.txt'")
    print("written midinote to file %s" % filename)


if __name__ == '__main__':
    print("this file is made to be imported as a module, not executed")
    raise SystemError
