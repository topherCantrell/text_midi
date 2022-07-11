import serial
#import time

ser = serial.Serial('COM6', 57600, timeout=1) 

# F0 7D 00 c1 c2 c3 ...

chans = [1]

r = chr(0xF0)+chr(0x7D)+chr(0x00)
for c in chans:
    r = r + chr(c)
r = r + chr(0xF7)

ser.write(r)
     
raw_input("Press enter")
print "Channel set"
    