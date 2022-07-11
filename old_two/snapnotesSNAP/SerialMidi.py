# Nice for sending serial-midi straight through the prop-plug to the
# propeller controller

import serial
import time

def noteOn(chan, note, vel):    
    r = chr(0x90+chan)+chr(note)+chr(vel)    
    ser.write(r)
    
def noteOff(chan, note, vel):
    r = chr(0x80+chan)+chr(note)+chr(vel)    
    ser.write(r)
    
def setVolume(chan, vol):
    r = chr(0xB0+chan)+chr(7)+chr(vol)
    ser.write(r)
    
def setInstrument(chan, ins):
    r = chr(0xC0+chan)+chr(ins)
    ser.write(r)
    
def setMidiChannels(chans):
    r = chr(0xF0)+chr(0x7D)
    for c in chans:
        r = r + chr(c)
    r = r+chr(0xF7)
    ser.write(r)
    
ser = serial.Serial('COM5', 57600, timeout=1) 

#setMidiChannels([0,1,2,5,7])

noteOn(0,60,100)
time.sleep(1)
noteOff(0,60,0)
noteOn(0,62,100)
time.sleep(1)
noteOff(0,62,0)



#r = '\x90\x3C\x7F\x90\x40\x7F\x90\x43\x7F'
#ser.write(r)

#noteOn(0,60,100)
#noteOn(0,64,100)
#noteOn(0,67,100)

#time.sleep(5)

'''
setVolume(0,10)

noteOn(0,69,64)


time.sleep(0.5)
noteOff(0,69,64)

noteOn(0,70,64)
time.sleep(0.5)
noteOff(0,70,64)

noteOn(0,71,64)
time.sleep(0.5)
noteOff(0,71,64)

noteOn(0,72,64)
time.sleep(0.5)
noteOff(0,72,64)

noteOn(0,73,64)

f = open("Sample.txt","r")
for line in f:    
    
    i = line.index(":")
    line = line[0:i-1]
    hex = line.split()
    bytes = [int(hex[0],16),int(hex[1],16)]
    if len(hex)>2:
        bytes.append(int(hex[2],16))
    serdat = chr(bytes[0])+chr(bytes[1])
    if len(bytes)>2:
        serdat = serdat + chr(bytes[2])
    
    if line[0] == "8":
        print "Note Off"
        ser.write(serdat)
    elif line[0] == "9":
        print "Note On "+repr(bytes)
        if(bytes[2]<20):
            bytes[2] = 0
        ser.write(serdat)        
    elif line[0] == "B":
        print "Channel" 
        ser.write(serdat)
    elif line[0] == "C":
        print "Patch"
        ser.write(serdat)
    elif line[0] == "E":
        print "Blend"
        ser.write(serdat)
        
    else:
        print "Unknown: "+line
        break
    
    time.sleep(0.5)
        
f.close()

'''

raw_input("Press Enter to end")
