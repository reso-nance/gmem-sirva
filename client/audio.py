#!/usr/bin/env python3
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  client/audio.py
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
xrunCounter, xrunSum = 0, 0
startTime = datetime.now()
inputs = {"microphone":"system:capture_1", "analogIN": "system:capture_2"}
outputs = {"transducer":"system:playback_1", "analogOUT":"system:playback_2"}
alsaControls = {"microphone": "'Mic',0", "analogIN":"'Mic',1", "transducer":"'UMC202HD 192k Output',0", "analogOUT":"'UMC202HD 192k Output',1"}

def init(soundcard=soundcardName, sampleRate=96000, bufferSize=256,
         bufferCount=2, priority=70, timeout=2000, maxClients=16):
# ~ def init(soundcard=soundcardName, sampleRate=48000, bufferSize=1024,
         # ~ bufferCount=4, priority=70, timeout=2000, maxClients=16):
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
    client.activate()
    with client : 
        assert len(client.get_ports(is_physical=True, is_output=True)) >= 2
        assert len(client.get_ports(is_physical=True, is_input=True)) >= 2
        print("  jack client has been started")
        print("  inputs:",client.get_ports(is_output=True))
        print("  outputs",client.get_ports(is_input=True))
        if not clientStarted : clientStarted = True
        # ~ client.connect("system:capture_1","GMEM client:analogOutput")
        event.wait()
        # ~ close()

# will use jackd to connect hardware inputs to outputs
def route(OSCaddress, OSCargs):
    if len(OSCargs)!= 2 : return False
    input, output = OSCargs
    assert input in inputs and output in outputs
    if clientStarted :
        client.connect(inputs[input], outputs[output])
        return True
    else : return False
    
# registered on xrun, will keep track of the number of xrun occured since launch
def xrun_callback(delayedMicros):
    global xrunCounter, xrunSum
    xrunCounter+=1
    xrunSum += int(delayedMicros)
    xrunMean = int(xrunSum/xrunCounter)
    runningSince = datetime.now() - startTime
    print("total xruns : %i in %s (average delay of %i microseconds) " %(xrunCounter, str(runningSince), xrunMean))

# registered on jackd shutdown
def shutdown_callback(status, reason):
    global event
    print('JACK shutdown')
    print('  status:', status)
    print('  reason:', reason)
    event.set()

# play a wav file on the selected output using jack-play
def playFile(OSCaddress, OSCargs):
    if len(OSCargs) < 1 : return
    filename, output2 = OSCargs[0], None
    if len(OSCargs) == 1 : output = outputs["transducer"]
    elif len(OSCargs) == 2 : output = OSCargs[1]
    elif len(OSCargs) == 3 : output, output2 = OSCargs[1:]
    assert output in outputs
    if output2 and output2 != output: 
        assert output2 in outputs
        cmd = "JACK_PLAY_CONNECT_TO=system:playback_%d jack-play " + filename
    else : cmd="JACK_PLAY_CONNECT_TO=%s jack-play %s" % (outputs[output], filename)
    subprocess.Popen(cmd, shell=True)

# mute, unmute and toggle channels using amixer
def mute(OSCaddress, channels) :
    for channel in channels :
        OSCaddress = OSCaddress.replace("/","")
        assert channel in alsaControls
        assert OSCaddress in ("mute", "unmute", "toggle")
        # capture devices doesn't have a mute parameter in alsa but a cap/nocap. (toggle works just fine)
        if channel in ("microphone", "analogIN") and OSCaddress is not "toggle" :
            if OSCaddress == "mute" : OSCaddress = "nocap"
            elif OSCaddress == "unmute" : OSCaddress = "cap"
        cmd = "amixer -Dhw:%s -q set %s %s" % (soundcardName, alsaControls[channel], OSCaddress)
        subprocess.Popen(cmd, shell=True)

# set the volume of capture and playback devices using amixer
def setVolume(OSCaddress, OSCargs):
    print(OSCaddress, OSCargs)
    channel, volume = OSCargs
    assert channel in alsaControls
    assert volume in range(101)
    cmd = "amixer -Dhw:{} -q set {} {}%".format(soundcardName, alsaControls[channel], volume) #FIXME : outputs should use amixer sset Master 80%,20% to balance
    subprocess.Popen(cmd, shell=True)

def getVolumes():
    volumes = [0,0,0,0]
    findLine = lambda txt, delimiter : next(line for line in txt.splitlines() if line.startswith(delimiter))
    volumes[0] = getAmixerControl("Mic,0", "  Front Left: Capture")
    volumes[1] = getAmixerControl("Mic,1", "  Mono: Capture")
    volumes[2] = getAmixerControl("UMC202HD 192k Output", "  Front Left: Playback")
    volumes[3] = getAmixerControl("UMC202HD 192k Output", "  Front Right: Playback")
    return volumes
    
def getAmixerControl(control, delimiter) :
    cmd = "amixer -Dhw:{} get '".format(soundcardName) # controls can be listed by amixer -Dhw:U192k  scontents
    p = subprocess.Popen(cmd + control +"'", shell=True, stdout=subprocess.PIPE)
    out, err = p.communicate()
    out = out.decode("utf-8")
    line = next(line for line in out.splitlines() if line.startswith(delimiter)) # extract line beginning with delimiter
    line = int(line.split(" [")[1].split("%]")[0])# strip the number between brackets and convert it to int [94%] -> 94
    return line

# called when exiting
def close():    
    runningSince = datetime.now() - startTime
    runningSince = runningSince.total_seconds() / 3600
    xrunPerHour = xrunCounter / runningSince
    if xrunCounter > 0 : 
        print( "xruns stats : total %i xruns, %.02f xruns/h, mean duration : %i micros" % (xrunCounter, xrunPerHour, int(xrunSum/xrunCounter)) )
    client.deactivate()
    subprocess.Popen("pkill jackd", shell=True)
