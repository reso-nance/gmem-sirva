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
import jack, threading, subprocess, time, os
from datetime import datetime
import soundfile as sf
import OSCserver

soundcardName = "U192k" # soundcard name in ALSA, as listed by aplay -l
wavDir = "wav"
client, event, jackServerThread, connections = None, None, None, None
alsaIndex = None
clientStarted = False
isPlaying = False
xrunCounter, xrunSum = 0, 0
startTime = datetime.now()
inputs = {"microphone":"system:capture_1", "analogIN": "system:capture_2"}
outputs = {"transducer":"system:playback_1", "analogOUT":"system:playback_2"}
alsaControls = {"microphone": "'Mic',0", "analogIN":"'Mic',1", "transducer":"'UMC202HD 192k Output',0", "analogOUT":"'UMC202HD 192k Output',1"}
# ~ alsaOutputVolumes = {"transducer":0, "analogOUT":0} # outputs volumes are stored here to be restored when unmuted since these two channels are linked in alsa (left-right)
jackParameters={"soundcard":soundcardName, "sampleRate":96000, "bufferSize":256, "bufferCount":3, "priority":80, "timeout":2000, "maxClients":2048}
# ~ jackParameters={"soundcard":soundcardName, "sampleRate":48000, "bufferSize":128, "bufferCount":2, "priority":80, "timeout":2000, "maxClients":2048}


def init(soundcard, sampleRate, bufferSize, bufferCount, priority, timeout, maxClients):
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
def route(OSCaddress, OSCargs, tags, IPaddress):
    global client
    if len(OSCargs)!= 2 : return False
    input, output = OSCargs
    assert input in inputs and output in outputs
    print("routing %s to %s (%s => %s)" % (input, output, inputs[input], outputs[output]))
    if clientStarted :
        client.connect(inputs[input], outputs[output])
        return True
    else : return False

def disconnect(OSCaddress, OSCargs, tags, IPaddress):
    global client
    if clientStarted and len(OSCargs) == 2 :
        input, output = OSCargs
        if input in inputs and output in outputs : client.disconnect(inputs[input], outputs[output])

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
def playFile(command, OSCargs, tags, IPaddress):
    global isPlaying
    print("playfile", OSCargs)
    if len(OSCargs) < 1 : return
    filename, output2 = OSCargs[0], None
    if wavDir+"/" not in filename : filename = wavDir+"/"+filename
    if len(OSCargs) == 1 : output = outputs["transducer"]
    elif len(OSCargs) == 2 : output = outputs[OSCargs[1]]
    elif len(OSCargs) == 3 : output, output2 = outputs[OSCargs[1]], outputs[OSCargs[2]]
    if output2 and output2 != output: 
        cmd = "JACK_PLAY_CONNECT_TO=system:playback_%d jack-play " + filename
    else : cmd="JACK_PLAY_CONNECT_TO=%s jack-play %s" % (output, filename)
    if isPlaying : stop()
    isPlaying = True
    subprocess.Popen(cmd, shell=True)

def stop(command=None, OSCargs=None, tags=None, IPaddress=None):
    global isPlaying
    subprocess.Popen("pkill jack-play", shell=True)
    if isPlaying : isPlaying = False

# mute, unmute and toggle channels using amixer
def mute(OSCaddress, channels, tags, IPaddress) : #FIXME : muting of output channel must be done manually
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
def setVolume(OSCaddress=None, OSCargs=None, tags=None, IPaddress=None):
    print(OSCaddress, OSCargs)
    channel, volume = OSCargs
    if channel in alsaControls and volume in range(101) :
        volume = int(volume/100*60+40) # map 0~100 to 40~100 since in alsa a volume below 40% is pretty much inaudible
        print("setting volume %s to %i" %(channel, volume))
        if channel in ("transducer", "analogOUT"): # since output volumes are controlled by LR balance :
            transducer, analogOUT = getVolumes()[2:] # we need to get volume of both outputs
            outputsVolumes = {"transducer":transducer, "analogOUT":analogOUT} # store them into a dict
            outputsVolumes[channel] = volume # then replace the one we need
            cmd = "amixer -Dhw:{} -q set 'UMC202HD 192k Output' {}%,{}%".format(soundcardName, outputsVolumes["transducer"], outputsVolumes["analogOUT"]) # then set them both a the same time
        else : cmd = "amixer -Dhw:{} -q set {} {}%".format(soundcardName, alsaControls[channel], volume)
        subprocess.Popen(cmd, shell=True)
        OSCserver.refreshVolumes()

def getVolumes():
    volumes = [0,0,0,0]
    # ~ findLine = lambda txt, delimiter : next(line for line in txt.splitlines() if line.startswith(delimiter))
    volumes[0] = getAmixerControl("Mic,0", "  Front Left: Capture")
    volumes[1] = getAmixerControl("Mic,1", "  Mono: Capture")
    volumes[2] = getAmixerControl("UMC202HD 192k Output", "  Front Left: Playback")
    volumes[3] = getAmixerControl("UMC202HD 192k Output", "  Front Right: Playback")
    remap = lambda x : int((x-40)/60*100) # remap from 40~100 to 0~100
    map(remap, volumes)
    return volumes
    
def getAmixerControl(control, delimiter) :
    cmd = "amixer -Dhw:{} get '".format(soundcardName) # controls can be listed by amixer -Dhw:U192k  scontents
    p = subprocess.Popen(cmd + control +"'", shell=True, stdout=subprocess.PIPE)
    out, err = p.communicate()
    out = out.decode("utf-8")
    line = next(line for line in out.splitlines() if line.startswith(delimiter)) # extract line beginning with delimiter
    line = int(line.split(" [")[1].split("%]")[0])# strip the number between brackets and convert it to int [94%] -> 94
    return line
    
def delete(OSCaddress, args, tags, IPaddress):
    filePaths = [wavDir+"/"+arg for arg in args]
    for path in filePaths :
        if os.path.isfile(path) :
            os.remove(path)
            print("deleted file "+path)
        else : print("cannot delete file {} : not found".format(path))

# called when exiting
def close():
    global client
    runningSince = datetime.now() - startTime
    runningSince = runningSince.total_seconds() / 3600
    xrunPerHour = xrunCounter / runningSince
    if xrunCounter > 0 : 
        print( "xruns stats : total %i xruns, %.02f xruns/h, mean duration : %i micros" % (xrunCounter, xrunPerHour, int(xrunSum/xrunCounter)) )
    if client : client.deactivate()
    subprocess.Popen("pkill jackd", shell=True)
