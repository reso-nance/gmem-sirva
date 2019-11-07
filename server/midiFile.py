#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  server/midiFile.py
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

import mido, json, os
import OSCserver

midiFolder = "./midiFiles"
noteTranslator = {} # will be populated by midiNote:IP
readMidi = True

def updateNoteTranslator(knownClients):
    global noteTranslator
    noteTranslator = {}
    for client in knownClients.values() : noteTranslator.update({client["midiNote"]:client["IP"]})
    print("updated MIDI note translator :", noteTranslator)

def play(OSCaddress, args, tags, IPAddress):
    global noteTranslator, readMidi
    if not noteTranslator : importFromJson()
    try : 
        midiPath = midiFolder+"/"+args[0]
        if os.path.isfile(midiPath) :
            readMidi = True
            print("playing file %s" % midiPath)
            for msg in mido.MidiFile(midiPath).play():
                if not readMidi : return
                if msg.type == "note_on" :
                    if msg.note in noteTranslator :
                        OSCserver.sendOSC(noteTranslator[msg.note], "/noteOn", [msg.velocity])
    except KeyboardInterrupt : raise
    except Exception as e : print(e)
    
def stop(OSCaddress, args, tags, IPAddress) :
    global readMidi
    readMidi = False
    print("stopping midi file parsing")
    

def main(args):
    return 0

def delete(OSCaddress, args, tags, IPAddress):
    filePaths = [midiFolder+"/"+arg for arg in args]
    for filePath in filePaths :
        if os.path.isfile(filePath) : 
            os.remove(filePath)
            print("deleted file "+filePath)
        else : print("cannot delete file {} : not found".format(filePath))
        


if __name__ == '__main__':
    print("this file is made to be imported as a module, not executed")
    raise SystemError
