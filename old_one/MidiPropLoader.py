"""This module uploads new code to the SerialMIDI propeller.

The SerialMIDI.spin program includes the code to receive this upload
and program the EEPROM. Be sure the code you upload has the same
programmer or you won't be able to upload again!

The SerialMIDI.spin program listens for updates firmware updates through
a MIDI meta event.

You must connect the "Serial-Air Gateway" RF100 node to the COM port and
run this program to upload the firmware to the propeller over the air.

"""

#import serial
import sys
from snapconnect import snap
from NodeList import NODES

import logging

def getCommand(filename):    

    with open(filename,"rb") as f:
        data = []
        checksum = 0
        for _ in xrange(0x4000):
            t =  ord(f.read(1))
            checksum = checksum + t
            checksum = checksum & 0xFFFF
            data.append(t)
        
        #print checksum, (checksum>>8), (checksum&0xFF)
            
        # F0 7D 01 cm cl ...
        r = chr(0xF0)+chr(0x7D)+chr(0x01)+chr(checksum>>8)+chr(checksum&0xFF)   
        for d in data:
            r = r + chr(d)
        r = r + chr(0xF7)
            
        return r    

def uploadSerialMidiPropeller(port,filename):
    """Upload SerialMIDI firmware updates
            
    Args:
      port (str): The COM port. This is likely attached to an RF Engine
      filename (str): The spin eeprom file to upload
    
    """
    
    data = getCommand(filename)
    
    ser = serial.Serial('COM6', 57600, timeout=1) 
        
    for d in data:
        ser.write(chr(d))
        #time.sleep(0.001)        
        
data = ""
position = 0
nodeNum = None
 
def rpcSent(packet_id, future_use):
    global data,position,nodeNum    
    if position<len(data):
        toSend = len(data)-position
        if(toSend)>8:
            toSend = 8
        comm.data_mode(NODES[nodeNum],data[position:position+toSend])
        position = position + toSend   
        print "Sending next chunk. Left to send:"+str(len(data)-position)
   
def uploadSNAPConnectMidiPropeller(comm,nNum,filename):
    """Upload propeller code through MIDI Meta Event
    
    Args:
      comm (SnapConnect): the SNAPConnect instance
      nodeNum (int): the node number (see NodeList.py) 
      filename (string): the eeprom file to send      
      
    """
    global data,position,nodeNum
    nodeNum = nNum    
    data = getCommand(filename)
    postion = 0
    
    rpcSent(None,None)
    
if __name__ == "__main__":
    
    import platform
    import sys
    
    logging.basicConfig(level=logging.ERROR, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        
    comm = snap.Snap()
    comm.set_hook(snap.hooks.HOOK_RPC_SENT, rpcSent)
    
    if platform.system()=='Windows':       
        comm.open_serial(snap.SERIAL_TYPE_SNAPSTICK100,0)
    else:
        comm.open_serial(snap.SERIAL_TYPE_SNAPSTICK100,0)
        
    uploadSNAPConnectMidiPropeller(comm,int(sys.argv[1]),sys.argv[2])    
    
    while True:
        comm.poll()    
   
        