#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  client/OSCserver.py
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
import liblo
import solenoid

listenPort = 9000
sendPort = 8000
server = None
runServer = True

def unknownOSC(path, args, types, src):
    print("got message '%s' from '%s'" % (path, src.url))
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
        
    server.add_method("/solenoid", None, solenoid.actuate)
    server.add_method("/readAudio", None, unknownOSC)
    server.add_method(None, None, unknownOSC)
    
    while runServer : 
        server.recv(100)
    print("  OSC server has closed")

def sendOSC(IPaddress, command, args):
    print("sending OSC {} {} to {}".format(command, args, IPaddress))
    liblo.send((IPaddress, sendPort), command, args)


if __name__ == '__main__':
    print("this file is made to be imported as a module, not executed")
    raise SystemError
