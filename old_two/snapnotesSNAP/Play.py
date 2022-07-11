import pygame.midi
from snapconnect import snap

pygame.init()
pygame.midi.init() 

comm = snap.Snap()
comm.open_serial(snap.SERIAL_TYPE_RS232,3)

inp = pygame.midi.Input(1)

#bells = [
         #'\x03\xAC\x26', # BellR1
         #'\x04\x6D\xC2', # BellR4      
         #'\x00\x63\x33', # BellR5
         #'\x04\x00\x4A', # BellB1     
         #'\x03\xC4\x2D', # BellR3
         #'\x04\x6D\xBA', # BellW2
         #'\x04\xC7\x42', # BellW1
         #'\x00\x81\x77', # BellR2    
        #]

while True:
    comm.poll()
    if inp.poll():
        events = inp.read(1000)        
        for event in events:      
            print event[0]        
            r = ""
            for x in range(0,len(event[0])):
                r = r + chr(event[0][x])
            #addr = bells[event[0][1]%len(bells)]
            #comm.data_mode(addr,r)
            comm.mcast_data_mode(1,2,r)
            
            