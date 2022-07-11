# Plays a MIDI file over the air

# Routine to set the program (instrument) for a channel

#import serial
from snapconnect import snap
from NodeList import NODES

import binascii
import pygame.midi
import platform
import sys
from midi import MidiFile
from midi import MidiTools

import MusicParser

from midi.MidiEvents import MetaEvent

import logging

def noteOn(comm,chan, note, vel):    
    r = chr(0x90+chan)+chr(note)+chr(vel)    
    comm.mcast_data_mode(1,2,r)
    
def noteOff(comm,chan, note, vel):
    r = chr(0x80+chan)+chr(note)+chr(vel)    
    comm.mcast_data_mode(1,2,r)
    
def setVolume(comm,chan, vol):
    r = chr(0xB0+chan)+chr(7)+chr(vol)
    comm.mcast_data_mode(1,2,r)
    
def setInstrument(comm,chan, ins):
    r = chr(0xC0+chan)+chr(ins)
    comm.mcast_data_mode(1,2,r)    

guitarHeroData = ""

def guitarData(data):
    global guitarHeroData
    guitarHeroData = guitarHeroData + data    

def rpcSent(packet_id, future_use):
    pass

def handleMidiKeyboard(comm,inp):
    events = inp.read(1000)        
    for event in events:                   
        com = event[0][0]
        note = event[0][1]
        vel = event[0][2]                
        if(com==0x90 or com==0x80):
            com = com + (note%8)                    
        r = chr(com)+chr(note)+chr(vel)                     
        comm.mcast_data_mode(1,2,r)
        
masterTrack = None
trackPosition = 0
tickCount = 0

def handleMidiFile(comm):
    global masterTrack, trackPosition, tickCount
    
    #TODO: This is all temporary. Needs to run on a tick timer.
    
    if tickCount>0:
        # Still waiting for next event
        tickCount = tickCount - 1
        return
            
    evt = masterTrack[trackPosition]
    trackPosition = trackPosition+1
            
    if isinstance(evt,MetaEvent):
        return # ignore Meta events
            
    print evt.getText()            
    comm.mcast_data_mode(1,2,evt.getMidiBytes())
            
    # Ick, ick, ick. Use a real timer
    if trackPosition<len(masterTrack):
        tickCount = masterTrack[trackPosition].delta  * 300  

if __name__ == "__main__":
    
    logging.basicConfig(level=logging.ERROR, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        
    masterTrack = None
    if len(sys.argv) > 1:
        fname = sys.argv[1]
        if fname.endswith(".mid"):
            (time,tracks) = MidiFile.parseFile(fname)
        else:
            tracks = MusicParser.processMusic(sys.argv[1])   
    
        masterTrack = MidiTools.mergeTracks(tracks)
        
    tickCount = 0
    trackPosition = 0
    
    # MidiTools.printTrack(masterTrack)
            
    pygame.init()
    pygame.midi.init() 
    
    # MIDI keyboard
    inp = None
    if pygame.midi.get_count() > 2:        
        inp = pygame.midi.Input(1)    
                  
    comm = snap.Snap()
    comm.set_hook(snap.hooks.HOOK_RPC_SENT, rpcSent)
    comm.set_hook(snap.hooks.HOOK_STDIN, guitarData)
    
    if platform.system()=='Windows':       
        comm.open_serial(snap.SERIAL_TYPE_SNAPSTICK100,0)
    else:
        comm.open_serial(snap.SERIAL_TYPE_SNAPSTICK100,0)
        
    while True:
        
        comm.poll()
        
        if inp and inp.poll():
            handleMidiKeyboard(comm,inp)
            
        if len(guitarHeroData)>0:
            comm.mcast_data_mode(1,2,guitarHeroData)  
            guitarHeroData = ""
        
        if masterTrack and (trackPosition!=len(masterTrack)):
            handleMidiFile(comm)
               
            
        