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
# ~ import os, logging, subprocess, eventlet
import os, logging, subprocess
# ~ eventlet.monkey_patch() # needed to make eventlet work asynchronously with socketIO, 

mainTitle = "GMEM || CIRVA || Réso-nance"

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
    
    
# --------------- SOCKET IO EVENTS ----------------

@socketio.on('connect', namespace='/home')
def onConnect():
    print("client connected, session id : "+request.sid)

@socketio.on('disconnect', namespace='/home')
def onDisconnect():
    print("client disconnected")

@socketio.on('shutdown', namespace='/notifications')
def sck_shutdown():
    print("system shutdown called from frontend")
    subprocess.Popen("sleep 3; sudo shutdown now", shell=True)
    socketio.emit("redirect", "/shutdown", namespace='/notifications')
 
@socketio.on('volChanged', namespace='/home')
def setVolume(data):
    print("changed volumes for {} to {}".format(data["hostname"], data["volumes"]))
    

# --------------- FUNCTIONS ----------------

