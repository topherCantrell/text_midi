# Propeller Serial Port Loader (version 0.2)
# Chad George
# 10-31-06

import serial
import time
import string
import sys

CommErrorConnect = "CommErrorConnect"
CommErrorProgram = "CommErrorProgram"
CommErrorVerify = "CommErrorVerify"

Comm = serial.Serial()
CommPort = None

TxBuffSize = 256
RxBuffSize = 256

TxBuff = []
RxBuff = []
LFSR = 0
Version = 0
VersionMode = True
AbortMode = True
LongCount = 0


man_ex_1 = [0x00, 0x1B, 0xB7, 0x00, 0x00, 0xDE, 0x10, 0x00, 0x30, 0x00, 0x38,
            0x00, 0x18, 0x00, 0x3C, 0x00, 0x20, 0x00, 0x02, 0x00, 0x08, 0x00,
            0x00, 0x00, 0x37, 0x03, 0x3D, 0xD6, 0x1C, 0x37, 0x03, 0x3D, 0xD4,
            0x47, 0x3A, 0x2D, 0xC6, 0xC0, 0x3F, 0x91, 0xEC, 0x23, 0x04, 0x71,
            0x32, 0x00, 0x00, 0x00]


# Reset hardware on current comm port
def ResetHardware():
    if Comm.isOpen():
        Comm.setDTR(1)
        DelayMSec(25)
        Comm.setDTR(0)
        DelayMSec(100)
        Comm.flushInput()

# Find hardware on any comm port
def FindAnyHardware():
    global CommPort
    global CommErrorConnect
    
    if OpenComm(CommPort) and HardwareFound():
        return True
    
    for port in ValidCommPorts():
        if OpenComm(port) and HardwareFound():
                return True

    CommError(CommErrorConnect, "No Hardware Found")
    return False

# Check for hardware on current comm port
def HardwareFound():
    global AbortMode
    global LFSR
    global CommErrorConnect
    global Version
    
    if Comm.isOpen():
        try:
            AbortMode = False
            ResetHardware()
            TByte(0xF9)
            LFSR = ord('P')
            for i in range(250):
                TByte( IterateLFSR() | 0xFE )
            for i in range(250 + 8):
                TByte(0xF9)
            TComm()

            for i in range(250):
                if RBit(False, 100) <> IterateLFSR():
                    CommError(CommErrorConnect, "Hardware Lost")

            for i in range(8):
                Version = ((Version >> 1) & 0x7F) | (RBit(False, 50) << 7)
            
            if VersionMode:
                TLong(0)
                TComm()
                ResetHardware()
                CloseComm()

            AbortMode = True
            return True
        
        except CommErrorConnect:
            AbortMode = True
            return False
    return False

# Get hardware version
def GetHardwareVersion():
    global VersionMode

    VersionMode = True
    FindAnyHardware()

# Send a buffer of data to the hardware
def TalkToHardware(command, buffer):
    global VersionMode
    global CommErrorProgram
    global Version
    global CommPort

    print "Looking for hardware..."
    VersionMode = False
    FindAnyHardware()

    print "Found Propeller Version %s on %s" % (Version, CommPort)

    TLong(command)
    TComm;

    if command > 0:
        longcount = len(buffer) >> 2
        print "Sending program (%s Words)..." % longcount
        
        TLong(longcount)

        for x in range(0, longcount << 2, 4):
            long = (buffer[x] |
                    (buffer[x+1] << 8)  |
                    (buffer[x+2] << 16) |
                    (buffer[x+3] << 24))
                   
            TLong(long)
            
        TComm()

        print "Verifying RAM Checksum..."
        if RBit(True, 2500) == 1:
            CommError(CommErrorProgram, "RAM Checksum Error")

        if command > 1:
            print "Programming EEPROM..."
            if RBit(True, 5000) == 1:
                CommError(CommErrorProgram, "EEPROM Programming Error")

            print "Verifying EEPROM..."
            if RBit(True, 2500) == 1:
                CommError(CommErrorProgram, "EEPROM Verify Eerror")

    print "Done."
    CloseComm()
            
# Cycles the LFSR 
def IterateLFSR():
    global LFSR
    
    bit = LFSR & 1
    LFSR = ((LFSR << 1) & 0xFE) | (LFSR >> 7 ^
                                   LFSR >> 5 ^
                                   LFSR >> 4 ^
                                   LFSR >> 1) & 1 
    return bit

# Communication Routines

# Returns a list of comm ports to try to find hardware on
def ValidCommPorts():
    if sys.platform == "win32":
        return ["COM%d" % x for x in range(9,0,-1)]
    else:
        return ["/dev/ttyUSB%d" % x for x in range(9,0,-1)]

# Open a comm port at 115200 baud, 8-N-1
def OpenComm(port):
    global Comm
    global CommPort
    
    CloseComm()
    try:
        Comm.port = port
        CommPort = port
        Comm.baudrate = 115200
        Comm.timeout = 0
        Comm.open()                 # open port 115200-8-N-1
    except serial.SerialException:
        return False
    return True

# Close the comm port
def CloseComm():
    global Comm

    if Comm.isOpen():
        Comm.close()

# Handle a communications error
def CommError(error, msg):
    global Comm
    global AbortMode
    
    if Comm.isOpen():
       Comm.close()

    if AbortMode:
        print "%s: %s" % (error,msg)

    raise error, msg

def HardwareLostError():
    global CommErrorConnect
    
    CommError(CommErrorConnect, "Hardware Lost")

# Send the trasmit buffer to the hardware
def TComm():
    global TxBuff
    global Comm
    
    sbuff = ''.join(map(chr, TxBuff))
    if Comm.isOpen():
        Comm.write(sbuff)
    else:
        print "Sending..."
        for b in TxBuff:
            print "%02X" % b
        print
    TxBuff = []

# Add a byte to the transmit buffer
def TByte(x):
    global TxBuff
    global TxBuffSize
    
    TxBuff.append(x)
    if len(TxBuff) == TxBuffSize:
        TComm()
        
# Add encoded long (11 bytes) to transmit buffer        
def TLong(x):
    global TByte
    
    for i in range(11):
        TByte(0x92 |
              (-(i==10) & 0x60) |
              (x & 1) |
              ((x & 2) << 2) |
              ((x & 4) << 4) )
        x = x >> 3

# Receive response from hardware via echoed byte
def RBit(echo, timeout):
    global RxBuff
    global default_timer

    timeout = timeout / 1000.0
    start = default_timer()
    while (default_timer() - start) < timeout:
        if echo:
            TByte(0xF9)
            TComm()
            DelayMSec(25)
        if len(RxBuff) == 0:
            RComm()
        else:
            bit = RxBuff[0] - 0xFE
            del RxBuff[0]
            
            if (bit & 0xFE) == 0:
                return bit
            
            HardwareLostError()
    HardwareLostError()

def RComm():
    global RxBuff
    global Comm

    RxBuff = []
    if Comm.isOpen():
        RxBuff = map(ord, Comm.read(RxBuffSize))


# Miscellaneous Utility Routines

LoopDelayMode = False               
if sys.platform == "win32":
    default_timer = time.clock      # higher resolution for windows
else:
    default_timer = time.time       # higher resolution for others

def DelayMSec(ms):
    global LoopDelayMode
    global default_timer
    
    ms = ms / 1000.0

    if LoopDelayMode:
        start = default_timer()
        while (default_timer() - start) < ms:
            pass
    else:
        time.sleep(ms)