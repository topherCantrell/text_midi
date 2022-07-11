import serial
#import time

ser = serial.Serial('COM6', 57600, timeout=1) 

# F0 7D 01 cm cl ...

with open("D:/workspaceEE/snapnotesSNAP/spin/SerialMIDI.eeprom","rb") as f:
    data = []
    checksum = 0
    for _ in xrange(0x4000):
        t =  ord(f.read(1))
        checksum = checksum + t
        checksum = checksum & 0xFFFF
        data.append(t)
    
    print checksum, (checksum>>8), (checksum&0xFF)
        
    r = chr(0xF0)+chr(0x7D)+chr(0x01)+chr(checksum>>8)+chr(checksum&0xFF)        
    ser.write(r)
    for d in data:
        ser.write(chr(d))
        #time.sleep(0.001)    
     
raw_input("Wait for confirmation tone and press enter")
print "Programming complete "
    