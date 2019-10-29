#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  server/main.py
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

from threading import Thread
import eventlet, atexit, signal
import OSCserver, UI, clients

flaskBind = "10.0.0.1"
HTTPlisteningPort = 8080

oscServerThread = None

def exitCleanly():
    print("writing known clients to file")
    clients.writeToFile()
    print("exiting disconnected thread")
    clients.disconnectedThread = False
    print("exiting OSCserver thread")
    OSCserver.listenToOSC = False
    raise SystemExit

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, exitCleanly) # register this exitCleanly function to be called on sigterm
    atexit.register(exitCleanly) # idem when called from within this script
    # ~ eventlet.spawn(OSCserver.listen)
    oscServerThread = Thread(target=OSCserver.listen)
    oscServerThread.start()
    print("reading known clients from file")
    clients.readFromFile()
    print("initialising known clients")
    clients.init()
    print("starting check disconnect thread...")
    Thread(target=clients.checkDisconnected).start()
    print("starting up webserver on %s:%i..." %(flaskBind, HTTPlisteningPort))
    eventlet.spawn(UI.socketio.run, UI.app, {"host":flaskBind, "port":HTTPlisteningPort})
    try: UI.socketio.run(UI.app, host=flaskBind, port=HTTPlisteningPort)  # Start the asynchronous web server (flask-socketIO)
    except KeyboardInterrupt : exitCleanly()
    
