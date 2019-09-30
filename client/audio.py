#!/usr/bin/env python3
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  client/audio.py
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
#  Based on JACK-python thru_client example : https://jackclient-python.readthedocs.io/en/0.4.0/examples.html
#  itself being based on the "thru_client.c" example of JACK 2: http://github.com/jackaudio/jack2/blob/master/example-clients/thru_client.c
# jackd --realtime -dalsa -D -dhw:1 -r96000 -n2 -p128  --hwmon
# jackd -P70 -p16 -t2000 -dalsa -dhw:U192k -p128 -n3 -r96000 -s

# ~ import sys, signal, os, jack, threading, subprocess
import jack, threading, subprocess, time, queue
from datetime import datetime
import soundfile as sf

soundcardName = "U192k" # soundcard name in ALSA, as listed by aplay -l
client, event, jackServerThread, connections = None, None, None, None
alsaIndex = None
clientStarted = False
xrunCounter = 0
startTime = datetime.now()
inputs = {"microphone":"system:capture_1", "analogIN": "system:capture_2"}
outputs = {"transducer":"system:playback_1", "analogOUT":"system:playback_2"}
alsaControls = {"microphone": "'Mic',0", "analogIN":"'Mic',1", "transducer":"'UMC202HD 192k Output',0", "analogOUT":"'UMC202HD 192k Output',1"}

# ~ def init(soundcard=soundcardName, sampleRate=96000, bufferSize=64,
         # ~ bufferCount=4, priority=70, timeout=2000, maxClients=16):
def init(soundcard=soundcardName, sampleRate=48000, bufferSize=1024,
         bufferCount=4, priority=70, timeout=2000, maxClients=16):
    global client, event, jackServerThread, clientStarted
    # launching jack server
    jackServerCmd = "jackd --realtime -P{} -p{} -t{} -dalsa -dhw:{} -p{} -n{} -r{} &".format(priority, maxClients, timeout,soundcard, bufferSize, bufferCount, sampleRate)
    # ~ jackServerCmd = "jackd --realtime -dalsa -D -dhw:{} -p{} -n{} -r{} --hwmon  &".format(soundcard, bufferSize, bufferCount, sampleRate)
    print("starting JACK server ...")
    for i in range(3):
        jackServerThread = subprocess.Popen(jackServerCmd, shell=True)
        time.sleep(5)
        if jackServerThread.poll() is not None :
            print("  started")
            break
    else : 
         raise SystemError("JACK server will not start")
            
    # setting up the client
    print("setting up JACK client...")
    client = jack.Client("GMEM client")
    if client.status.server_started: print("connected to JACK server")
    if client.status.name_not_unique: print('unique name {0!r} assigned'.format(client.name))
    event = threading.Event()
    client.set_xrun_callback(xrun_callback)
    client.set_shutdown_callback(shutdown_callback)
    client.set_process_callback(processRouting_callback)
    # create two port pairs
    # ~ client.outports.register("micInput")
    # ~ client.outports.register("analogInput")
    # ~ client.inports.register("transducerOutput")
    # ~ client.inports.register("analogOutput")
    # ~ print("  4 IOs registered")
    client.activate()
    with client : 
        assert len(client.get_ports(is_physical=True, is_output=True)) >= 2
        assert len(client.get_ports(is_physical=True, is_input=True)) >= 2
        print("inputs:",client.get_ports(is_output=True))
        print("outputs",client.get_ports(is_input=True))
        if not clientStarted : clientStarted = True
        # ~ client.connect("system:capture_1","GMEM client:analogOutput")
        event.wait()
        # ~ close()
    
# ~ def connect():
    # ~ if clientStarted :
         # ~ client.connect("system:capture_1","system:playback_1")
         # ~ client.connect("system:capture_2","system:playback_2")
         # ~ return True
    # ~ else : return False
    
def connect(input, output):
    assert input in inputs and output in outputs
    if clientStarted :
        client.connect(inputs[input], outputs[output])
        return True
    else : return False
    
def xrun_callback(delayedMicros):
    global xrunCounter
    xrunCounter+=1
    runningSince = datetime.now() - startTime
    print("total xruns : %i in %s (delay of %i microseconds) " %(xrunCounter, str(runningSince), int(delayedMicros)))

def shutdown_callback(status, reason):
    global event
    print('JACK shutdown!')
    print('  status:', status)
    print('  reason:', reason)
    event.set()

def processRouting_callback(frames):
        assert len(client.inports) == len(client.outports)
        assert frames == client.blocksize
        for i, o in zip(client.inports, client.outports):
            o.get_buffer()[:] = i.get_buffer()

def playFile(fileName, output=outputs["transducer"], output2 = None):
    assert output in outputs
    if output2 and output2 != output: 
        assert output2 in outputs
        cmd = "JACK_PLAY_CONNECT_TO=system:playback_%d jack-play " + fileName
    else : cmd="JACK_PLAY_CONNECT_TO=%s jack-play %s" % (outputs[output], fileName)
    subprocess.Popen(cmd, shell=True)

def mute(OSCaddress, channels) :
    for channel in channels :
        OSCaddress = OSCaddress.replace("/","")
        assert channel in alsaControls
        assert OSCaddress in ("mute", "unmute", "toggle")
        if channel in ("microphone", "analogIN") and OSCaddress is not "toggle" :
            if OSCaddress == "mute" : OSCaddress = "nocap" # inputs doesn't have a mute parameter in alsa but a cap/nocap. Toggle works just fine
            elif OSCaddress == "unmute" : OSCaddress = "cap"
        cmd = "amixer -Dhw:%s -q set %s %s" % (soundcardName, alsaControls[channel], OSCaddress)
        subprocess.Popen(cmd, shell=True)

def setVolume(OSCaddress, OSCargs):
    print(OSCaddress, OSCargs)
    channel, volume = OSCargs
    assert channel in alsaControls
    assert volume in range(101)
    cmd = "amixer -Dhw:{} -q set {} {}%".format(soundcardName, alsaControls[channel], volume)
    subprocess.Popen(cmd, shell=True)

def getAlsaIndex(soundcardName):
    info = subprocess.check_output(["aplay", "-l"]).decode("utf-8")
    for line in info.splitlines() :
        if line.count(soundcardName) :
            ALSAindex = (line.split("card "))[1].split(": Device")[0]
            ALSAindex = int(ALSAindex)
            return ALSAindex
    raise SystemError(info + "\nSoundcard not found in ALSA devices")

def close():
     client.deactivate()
     subprocess.Popen("pkill jackd", shell=True)
     raise SystemExit
