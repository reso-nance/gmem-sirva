#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  main.py
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
import midiFiles

port = 8000
server = None

def main(args):
    return 0

def unknownOSC(path, args, types, src):
    print("got message '%s' from '%s'" % (path, src.url))
    for a, t in zip(args, types):
        print ("  argument of type '%s': %s" % (t, a))

def start():
	global server
	
	try:
		server = liblo.Server(portNumber)
		print("listening on "+server.url)
	except liblo.ServerError as err:
		print(str(err))
		raise SystemExit
		
	server.add_method("/readMidi", None, printOSC)
	server.add_method("/readAudio", None, printOSC)
	server.add_method(None, None, printOSC)
	
	while True : 
		server.recv(100)

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
