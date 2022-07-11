from MidiEvents import MetaEvent
from MidiEvents import ContinuationEvent
from MidiEvents import MidiEvent

"""MIDI File Handling

This module contains functions for reading and writing a MIDI file

"""

def readFourBytes(f):
    dat = f.read(4)
    return (ord(dat[0])<<24) | (ord(dat[1])<<16) | (ord(dat[2])<<8) | ord(dat[3])

def writeFourBytes(f, num):
    f.write(chr((num>>24) & 255))
    f.write(chr((num>>16) & 255))
    f.write(chr((num>>8) & 255))
    f.write(chr((num) & 255))    

def readTwoBytes(f):
    dat = f.read(2)
    return (ord(dat[0])<<8) | ord(dat[1])

def writeTwoBytes(f,num):
    f.write(chr((num>>8) & 255))
    f.write(chr((num) & 255))    

def readByte(f):
    return ord(f.read(1))

def writeByte(f,num):
    f.write(chr(num))

def readDelta(f):
    ret = 0
    while True:
        v = readByte(f)
        ret = (ret << 7) | (v & 0x7F)
        if v<0x80:
            return ret
        
def writeDelta(f,delta):
    pass        

def readHeaderChunk(f):
    dat = f.read(4)
    if dat!="MThd":
        raise Exception("Missing 'MThd' header") 
    en = readFourBytes(f)
    if en!=6:
        raise Exception("Expected header length to be 6 bytes but got "+str(en))
    format = readTwoBytes(f)
    numTracks = readTwoBytes(f)
    divis = readTwoBytes(f)
    print format,numTracks,divis
    return (format,numTracks,divis)

def readTrackChunk(f,num):
    
    ret = []
    
    dat = f.read(4)
    if dat!="MTrk":
        raise Exception("Missing 'MTrk' header")
    trackSize = readFourBytes(f)    
    
    eot = f.tell()+trackSize
    
    prev = None
    
    while f.tell()!=eot:
        delta = readDelta(f)        
    
        d = readByte(f)
        if(d==0xFF):
            t = readByte(f)
            tl = readDelta(f)
            td = f.read(tl)
            e = MetaEvent(delta,t,td)
            ret.append(e)
            continue
        
        com = d>>4
        chan = d&0xF
        
        if com<8:
            e = readByte(f)
            e = ContinuationEvent(delta,prev,[d,e])
            ret.append(e)            
            continue
        elif com==8:
            nn = readByte(f)
            ve = readByte(f)
            e = MidiEvent(delta,chan,"NoteOff",[d,nn,ve])
            prev = e
            ret.append(e)
            continue
        elif com==9:
            nn = readByte(f)
            ve = readByte(f)
            e = MidiEvent(delta,chan,"NoteOn",[d,nn,ve])
            prev = e
            ret.append(e)
            continue
        elif com==10:
            raise Exception("OOPS")
        elif com==11:
            cn = readByte(f)
            va = readByte(f)
            e = MidiEvent(delta,chan,"ControllerChange",[d,cn,va])
            prev = e
            ret.append(e)
            continue
        elif com==12:
            prg = readByte(f)
            MidiEvent(delta,chan,"ProgramChange",[d,prg])
            prev = e
            ret.append(e)
            continue
        elif com==13:
            raise Exception("OOPS")
        elif com==14:
            raise Exception("OOPS")
        elif com==15:
            raise Exception("OOPS")        
        
        print com,chan
        raise Exception("Implement me")
    
    return ret
    
def parseFile(filename):
    with open(filename,"rb") as f:
        (_,numTracks,time) = readHeaderChunk(f)
            
        tracks = []    
        for n in xrange(numTracks):    
            events = readTrackChunk(f,n)
            tracks.append(events)
        
        return (time,tracks)
    
def writeFile(filename,time,tracks):
    # ** Header chunk is
    # MThd           ' 4 bytes
    # 00 00 00 06    ' 6 more bytes in header
    # 00 01          ' Format
    # 00 nn          ' Number of tracks
    # dd dd          ' Division
    
    # ** Each Track
    # MTrk
    # ss ss ss ss    ' Size
    # delta/event ...
    pass