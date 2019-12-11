#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  server/UI.py
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
from flask import Flask, g, render_template, redirect, request, url_for, copy_current_request_context, send_file, flash, Markup, Response
from flask_socketio import SocketIO, emit
from flask_uploads import UploadSet, configure_uploads, UploadNotAllowed
# ~ import os, logging, subprocess, eventlet
import os, logging, subprocess, urllib.parse, glob, json
import clients, OSCserver
# ~ eventlet.monkey_patch() # needed to make eventlet work asynchronously with socketIO, 

mainTitle = "GMEM || CIRVA || Réso-nance"
midiFilesDir = "./midiFiles"
audioFilesDir = "./tmp"
uploadedFile = None

if __name__ == '__main__':
    raise SystemExit("this file is made to be imported as a module, not executed")

# Initialize Flask and flask-socketIO
app = Flask(__name__) 
app.url_map.strict_slashes = False # don't terminate each url by / ( can mess with href='/#' )
# ~ socketio = SocketIO(app, async_mode="eventlet")
socketio = SocketIO(app, async_mode="threading", ping_timeout=36000)# set the timeout to ten hours, defaut is 60s and frequently disconnects
# disable flask debug (except errors)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
# flask-upload
audioFiles = UploadSet(name='audioFiles', extensions=('wav', 'WAV', 'Wav', 'mp3', 'MP3', 'Mp3', 'ogg', 'OGG', 'Ogg'))
app.config['UPLOADED_AUDIOFILES_DEST'] = audioFilesDir
midiFiles = UploadSet(name='audioFiles', extensions=('MID', 'mid', 'Mid'))
app.config['UPLOADED_MIDIFILES_DEST'] = midiFilesDir
configure_uploads(app, (audioFiles, midiFiles))
uploadSets={"audio":audioFiles, "midi": midiFiles}

# --------------- FLASK ROUTES ----------------

@app.route('/')
def rte_homePage():
    general_Data = {'title':mainTitle}
    return render_template('index.html', **general_Data)

@app.route('/shutdown')
def rte_bye():
    general_Data = {'title':mainTitle}
    return render_template('shutdown.min.html', **general_Data)   
     
@app.route('/onlineTracker<ID>.jpg')
def rte_trk(ID):
    filePath = os.path.abspath(os.path.dirname(__file__)) + "/static/trk.jpg"
    return send_file(filePath, mimetype='image/jpg')
    
# @app.route('/uploadAudio/<string:hostname>', methods=['GET', 'POST'])
# def rte_uploadAudio(hostname):
@app.route('/uploadAudio', methods=['GET', 'POST'])
def rte_uploadAudio():
    global uploadedFile
    if request.method == 'POST' and 'audiofile' in request.files:
        # hostname = urllib.parse.unquote(hostname)
        # if hostname not in clients.knownClients or clients.knownClients[hostname]["connected"] == False and hostname != "server":
        #     print("tried to send an audio file to an unknown or disconnected host :" + hostname)
        #     return('<script>alert("Erreur : l\'appareil sélectionné n\'est pas en ligne");window.location = "/";</script>')
        try :
            filename = uploadSets["audio"].save(request.files['audiofile'])
            print("successfully uploaded audio "+filename)
            uploadedFile = filename
        except UploadNotAllowed:
            print("ERROR : this file is not an audio file ")
            socketio.emit("uploadNotAllowed")
            return('<script>alert("Erreur : le fichier selectionné n\'est pas un fichier wav ou mp3");window.location = "/";</script>')
        return redirect('#')



@app.route('/uploadMidi', methods=['GET', 'POST'])
def rte_uploadMidi():
    if request.method == 'POST' and "midifile" in request.files:
        # ~ deviceID = urllib.parse.unquote(hostname)
        try :
            filename = uploadSets["midi"].save(request.files['midifile'])
            print("successfully uploaded midi "+filename)
        except UploadNotAllowed:
            print("ERROR : this file is not a midi file ")
            return('<script>alert("Erreur : le fichier selectionné n\'est pas un fichier midi");window.location = "/";</script>')
        return redirect('#')
    
# --------------- SOCKET IO EVENTS ----------------

@socketio.on('connect', namespace='/home')
def onConnect():
    global uploadedFile
    print("client connected, session id : "+request.sid)
    refreshDeviceList()
    sendMidiFileList()
    if uploadedFile : 
        socketio.emit("uploadSuccessful", uploadedFile, namespace="/home")
        uploadedFile = None

@socketio.on('disconnect', namespace='/home')
def onDisconnect():
    print("client disconnected")
 
@socketio.on('volChanged', namespace='/home')
def setVolume(data):
    volName = ["microphone", "analogIN", "transducer", "analogOUT"][data["index"]]
    clients.sendOSC(data["hostname"], "/volume", [volName, data["volume"]])
    print("changed volumes for {}:{} to {}".format(data["hostname"], volName, data["volume"]))

@socketio.on('midiNoteChanged', namespace='/home')
def changeMidiNote(data):
    clients.changeParameter(data["hostname"], "midiNote", data["midinote"])
    
@socketio.on("hostnameChanged", namespace="/home")
def changeHostname(data):
    clients.changeHostname(data["hostname"], data["newHostname"])
    
@socketio.on("playFile", namespace="/home")
def playFile(data):
    clients.sendOSC(data["hostname"], "/play", [urllib.parse.unquote(data["fileSelected"])])
    
@socketio.on("stopFile", namespace="/home")
def stopFile(hostname):
    hostname = urllib.parse.unquote(hostname)
    clients.sendOSC(hostname, "/stop")  

@socketio.on("deleteFile", namespace="/home")
def deleteFile(data):
    clients.sendOSC(data["hostname"], "/delete", [urllib.parse.unquote(data["fileSelected"])])
    
@socketio.on("playMidi", namespace="/home")
def playMidi(fileName):
    fileName = urllib.parse.unquote(fileName)
    OSCserver.sendOSCtoLocalhost("/readMidi", [fileName])

@socketio.on("stopMidi", namespace="/home")
def stopMidi(fileName):
    fileName = urllib.parse.unquote(fileName)
    OSCserver.sendOSCtoLocalhost("/stopMidi", [fileName])
    
@socketio.on("deleteMidi", namespace="/home")
def deleteMidi(fileName):
    fileName = urllib.parse.unquote(fileName)
    OSCserver.sendOSCtoLocalhost("/delete", [fileName])
    sendMidiFileList()
    
@socketio.on("midiAction", namespace="/home")
def midiAction(data):
    fileName = urllib.parse.unquote(data["fileName"])
    OSCserver.sendOSCtoLocalhost("/"+data["action"], [fileName])
    
@socketio.on("dispatchFileToClients", namespace="/home")
def dispatchFileToClients(data):
    filename = urllib.parse.unquote(data["filename"])
    clientList = [urllib.parse.unquote(c) for c in data["clientList"]]
    if os.path.isfile(audioFilesDir+"/"+filename) :
        for hostname in clientList : sendFileToClient(filename, hostname)
        os.remove(audioFilesDir+"/"+filename)
    else : print("ERROR dispatching %s to %s : file not found"%(filename, hostname))

@socketio.on("refreshClients", namespace="/home")
def refreshClients():
    print("asked from UI to refresh client list")
    clients.forgetAll(clearCache=True)

@socketio.on("shutdown", namespace="/home")
def shutdownFromUI():
    print("shutdown called from frontend")
    OSCserver.shutdown()
    
# --------------- FUNCTIONS ----------------

def refreshDeviceList():
    socketio.emit("deviceList", clients.knownClients, namespace='/home')
    print("updated UI device list")

def refreshVolumes(command, args, tags, IPaddress):
    IP = IPaddress.url.split("//")[1].split(":")[0] # retrieve IP from an url like osc.udp://10.0.0.12:35147/
    for client in clients.knownClients.values():
        if client["IP"] == IP :
            hostname = client["name"]
            print("refreshing UI volumes for client {} : {}".format(hostname, args))
            clients.knownClients[hostname]["volumes"] = args
            socketio.emit("refreshVolumes", {"hostname":hostname, "volumes":args}, namespace='/home')

def refreshFileList(hostname, fileList):
    socketio.emit("updateFileList", {"hostname":hostname, "fileList":fileList}, namespace='/home')

def sendMidiFileList():
    midiFilesList = []
    for ext in ("mid", "MID", "Mid") : midiFilesList += glob.glob(midiFilesDir+"/*."+ext)
    midiFilesList = [f.replace(midiFilesDir+"/", "") for f in midiFilesList] # remove dir name from fileList
    socketio.emit("midiFilesList", midiFilesList, namespace='/home')

def sendFileToClient(filename, hostname):
    tries = 0
    while tries < 4 :
        cmd = "sshpass -p raspberry scp -oStrictHostKeyChecking=no %s/%s pi@%s.local:/home/pi/client/wav/" % (audioFilesDir, filename, hostname)
        os.system('ssh-keygen -f "/home/pi/.ssh/known_hosts" -R "'+hostname+'.local"')
        if os.system(cmd) == 0 : 
            print("succesfully dispatched %s to %s"%(filename, hostname))
            socketio.emit("successfullDispatch",{"filename":filename, "hostname":hostname}, namespace = "/home")
            clients.sendOSC(hostname, "/getFileList") # to update the fileList on the UI
            return True
        else : tries+=1
    print("dispatching of %s to %s via sFTP failed 3 times in a row"%(filename, hostname))
    socketio.emit("dispatchFailed",{"filename":filename, "hostname":hostname}, namespace = "/home")
    return False
