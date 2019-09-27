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
import jack, threading, subprocess, time

soundcardName = "U192k" # soundcard name in ALSA, as listed by aplay -l
client, event, jackServerThread = None, None, None
clientStarted = False

def init(soundcard=soundcardName, sampleRate=48000, bufferSize=128,
         bufferCount=3, priority=70, timeout=2000, maxClients=16):
    global client, event, jackServerThread, clientStarted
    # launching jack server
    # ~ jackServerCmd = "jackd --realtime -P{} -p{} -t{} -dalsa -dhw:{} -p{} -n{} -r{} -s &".format(priority, maxClients, timeout,soundcard, bufferSize, bufferCount, sampleRate)
    jackServerCmd = "jackd --realtime -p{} -t{} -dalsa -dhw:{} -p{} -n{} -r{} -s --hwmon &".format(maxClients, timeout,soundcard, bufferSize, bufferCount, sampleRate)
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
    # create two port pairs
    # ~ client.outports.register("micInput")
    # ~ client.outports.register("analogInput")
    # ~ client.inports.register("transducerOutput")
    # ~ client.inports.register("analogOutput")
    # ~ print("  4 IOs registered")
    @client.set_process_callback
    def process(frames):
        assert len(client.inports) == len(client.outports)
        assert frames == client.blocksize
        for i, o in zip(client.inports, client.outports):
            o.get_buffer()[:] = i.get_buffer()

    @client.set_shutdown_callback
    def shutdown(status, reason):
        print('JACK shutdown!')
        print('  status:', status)
        print('  reason:', reason)
        event.set()
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
    
def connect():
    if clientStarted :
         client.connect("system:capture_1","system:playback_1")
         client.connect("system:capture_2","system:playback_2")
         return True
    else : return False

def fixme() :
    global client
    with client:
        # When entering this with-statement, client.activate() is called.
        # This tells the JACK server that we are ready to roll.
        # Our process() callback will start running now.

        # Connect the ports.  You can't do this before the client is activated,
        # because we can't make connections to clients that aren't running.
        # Note the confusing (but necessary) orientation of the driver backend
        # ports: playback ports are "input" to the backend, and capture ports
        # are "output" from it.
        capture = client.get_ports(is_physical=True, is_output=True)
        if not capture:
            raise RuntimeError('No physical capture ports')

        for src, dest in zip(capture, client.inports):
            client.connect(src, dest)

        playback = client.get_ports(is_physical=True, is_input=True)
        if not playback:
            raise RuntimeError('No physical playback ports')

        for src, dest in zip(client.outports, playback):
            client.connect(src, dest)

        print('Press Ctrl+C to stop')
        try:
            event.wait()
        except KeyboardInterrupt:
            print('\nInterrupted by user')
    # When the above with-statement is left (either because the end of the
    # code block is reached, or because an exception was raised inside),
    # client.deactivate() and client.close() are called automatically.

def close():
     client.deactivate()
     subprocess.Popen("pkill jackd", shell=True)
     raise SystemExit
