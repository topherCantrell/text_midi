"""Set the active-channels on the SerialMIDI propeller node

"""

#import serial
from snapconnect import snap
from NodeList import NODES

import logging

def getMIDIChannelSetCommand(chans=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]):
    """Build the MIDI meta command to set the channel list.
    
    Args:
      chans (int []): list of active channels for the node
      
    Returns:
      the string of midi characters
    
    """
    
    # This is the MIDI sequence: F0 7D 00 c1 c2 c3 ... F7
    
    ret = chr(0xF0)+chr(0x7D)+chr(0x00)
    
    for c in chans:
        ret = ret + chr(c)
        
    ret = ret + chr(0xF7)
    
    return ret

def setChannelsSerial(port,chans=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]):
    """Set the active-channel list in the serial-connected node.
    
    Args:
      port (str): the COM port
      chans (int []): list of active channels for the node
      
    """

    r = getMIDIChannelSetCommand(chans)
    ser = serial.Serial(port, 57600, timeout=1)
    ser.write(r)
    

def rpcSent(packet_id, future_use):
    #print "GOT A SENT"
    pass
    
def setChannelsMultiNodesSNAPConnect(comm, nodeChans):
    for (nodeNum,chans) in nodeChans.iteritems():
        setChannelsSNAPConnect(comm,nodeNum,chans)
        # TODO: This may require using the rpcSent hook in case we fill the send buffer
    
def setChannelsSNAPConnect(comm, nodeNum, chans):
    """Set the active-channel list in the target node 
    using SNAPConnect.
    
    Args:
      comm (SnapConnect): the SNAPConnect instance
      nodeNum (int): the node number (see NodeList.py)
      chans (int []): list of active channels for the node
      
    """
    
    print nodeNum,chans
    command = getMIDIChannelSetCommand(chans)
    comm.data_mode(NODES[nodeNum],command)
    
    mask = 0
    for c in chans:
        mask = mask | (1<<c)    
    
    comm.rpc(NODES[nodeNum], 'setUnitChannels', mask)   
         
if __name__ == "__main__":
    
    import platform
    import sys
    
    logging.basicConfig(level=logging.ERROR, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    d = {}
    
    for param in sys.argv[1:]:
        i = param.index("=")
        nodeNum = int(param[0:i])
        chs = param[i+1:].split(",")   
        chans = []
        for c in chs:
            chans.append(int(c))
        d[nodeNum] = chans
            
    comm = snap.Snap()
    comm.set_hook(snap.hooks.HOOK_RPC_SENT, rpcSent)
    
    if platform.system()=='Windows':       
        comm.open_serial(snap.SERIAL_TYPE_SNAPSTICK100,0)
    else:
        comm.open_serial(snap.SERIAL_TYPE_SNAPSTICK100,0)
        
    setChannelsMultiNodesSNAPConnect(comm, d)    
    
    while True:
        comm.poll()
        