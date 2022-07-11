"""Midi input-device to serial midi over the air

This script reads serial input events from an attached device
and broadcasts the events over the air to any midi players.

"""

import pygame.midi
from snapconnect import snap

pygame.init()
pygame.midi.init() 

comm = snap.Snap()
comm.open_serial(snap.SERIAL_TYPE_RS232,3)

inp = pygame.midi.Input(1)

while True:
    comm.poll()
    if inp.poll():
        events = inp.read(1000)        
        for event in events:      
            print event[0]        
            r = ""
            for x in range(0,len(event[0])):
                r = r + chr(event[0][x])            
            comm.mcast_data_mode(1,2,r)
            
            