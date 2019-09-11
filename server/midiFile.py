#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  server/midiFile.py
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

import mido, json, os
import OSCserver

midiToHostnames = "midi-hostnames.json"
midiFolder = "./midiFiles"
noteTranslator = None
defaultNoteTranslator = {50:"gmemClientTest"} # 60 is middle C

def exportToJson(data):
	with open (midiToHostnames, "w") as f : json.dump(data, f)

def importFromJson():
	global noteTranslator
	if os.path.isfile(midiToHostnames): 
		with open(midiToHostnames, "r") as fp: noteTranslator = json.load(fp)
	else :
		print("file %s not found, switching back to defaults" % midiToHostnames)
		noteTranslator = defaultNoteTranslator
		exportToJson(defaultNoteTranslator)

def play(path, args, types, src):
	global noteTranslator
	if not noteTranslator : importFromJson()
	try : 
		midiPath = midiFolder+"/"+args[0]
		if os.path.isfile(midiPath) :
			print("playing file %s" % midiPath)
			for msg in mido.MidiFile(midiPath).play(): 
				if msg.type == "note_on" :
					if msg.note in noteTranslator :
						OSCserver.sendOSC(noteTranslator[msg.note]+".local", "solenoid", [msg.velocity])
	except KeyboardInterrupt : raise
	except Exception as e : print(e)
	

def main(args):
    return 0


if __name__ == '__main__':
    print("this file is made to be imported as a module, not executed")
    raise SystemError
