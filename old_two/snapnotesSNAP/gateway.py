import pygame.midi
import sys
from snapconnect import snap
import socket
import select
import json

import binascii

mpkMiniID = -1
midiIn = None

def openMIDI():
    global mpkMiniID,midiIn
    mpkMiniID = -1
    numdev = pygame.midi.get_count()
    for i in xrange(numdev):
        (interface, name, input, output, opened) = pygame.midi.get_device_info(i)
        print interface, name, input, output, opened
        if name=="MPK mini" and input==1:
            mpkMiniID = i   
    if mpkMiniID >=0:     
        midiIn = pygame.midi.Input(mpkMiniID)

pygame.init()
pygame.midi.init() 

# Get ready for SNAP communication
print "Connecting to SNAP bridge ..."
comm = snap.Snap()
#comm.open_serial(snap.SERIAL_TYPE_RS232,"/dev/ttyUSB0")
comm.open_serial(snap.SERIAL_TYPE_RS232,3)

# Get ready for MIDI input (if available)
print "Connecting to MPKmini MIDI device ..."
openMIDI()

# Make a socket for the web server
print "Listening for JSON connectors (the web server) ..."
jsonServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
jsonServer.bind(("0.0.0.0",1234))
jsonServer.listen(5)
jsonSocket = None

jsonBuffer = ""


# TODO: How to config this? On the fly? From a file? Web page?
bells = [         
         #'\x04\x6D\xC2', # Pipe1  OK
         #'\x04\x6D\xBA', # Pipe2  OK
         #'\x03\xAC\x26', # Pipe3  Sticky switch
         #'\x03\xC4\x2D', # Pipe4  Sticky switch
         '\x00\x63\x33', # Pipe5  OK
         #'\x04\x00\x4A', # Pipe6  OK
         #'\x00\x81\x77', # Pipe7
         #'\x04\xC7\x42', # Pipe8             
        ]

def handleMIDI():
    if midiIn.poll():
        events = midiIn.read(1000)        
        for event in events:      
            print event[0]        
            r = ""
            for x in range(0,len(event[0])):
                r = r + chr(event[0][x])
            addr = bells[event[0][1]%len(bells)]
            comm.data_mode(addr,r)
            
def handleJSONSocket():
    global jsonSocket,jsonServer,jsonBuffer
    if jsonSocket == None:
        readable, writeable, errored = select.select([jsonServer], [], [], 0) #poll
        if len(readable)>0:            
            (jsonSocket,address) = jsonServer.accept()
            print "Accepted JSON connection on",jsonSocket  
        return
    readable,writeable,errored = select.select([jsonSocket], [], [], 0) #poll
    if len(readable)>0:
        data = jsonSocket.recv(4096)
        #print "data",binascii.hexlify(data)
        jsonBuffer = jsonBuffer + data
        if "\n" in jsonBuffer:
            i = jsonBuffer.index("\n")
            command = jsonBuffer[0:i]            
            jsonBuffer = jsonBuffer[i+1:]
            jsonFromServer(command)
             
def jsonFromServer(j):
    #print "Command to server:"+binascii.hexlify(j)+":"
    obj = json.loads(j)
    print obj
    
def jsonToServer(j):
    print "Command to server:"+j+":"
    
 
print "Starting Main Loop"
while True:
    comm.poll()
    handleMIDI()
    handleJSONSocket()
