#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  OSCserver.py
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

# ~ socket.gethostbyname('goosdfdsfdsfgle.com')
# ~ Traceback (most recent call last):
  # ~ File "<stdin>", line 1, in <module>
# ~ socket.gaierror: [Errno -2] Name or service not known

import liblo
import midiFile

listenPort = 8000
sendPort = 9000
server = None

def main(args):
    return 0

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
        
    server.add_method("/readMidi", None, midiFile.play)
    server.add_method("/readAudio", None, unknownOSC)
    server.add_method(None, None, unknownOSC)
    
    while True : 
        server.recv(100)

def sendOSC(IPaddress, command, args):
    print("sending OSC {} {} to {}".format(command, args, IPaddress))
    liblo.send((IPaddress, sendPort), command, args)


if __name__ == '__main__':
    print("this file is made to be imported as a module, not executed")
    raise SystemError
