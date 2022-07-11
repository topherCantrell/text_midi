from MidiEvents import MetaEvent
from MidiEvents import ContinuationEvent
from MidiEvents import MidiEvent

def readFourBytes(f):
    dat = f.read(4)
    return (ord(dat[0])<<24) | (ord(dat[1])<<16) | (ord(dat[2])<<8) | ord(dat[3])

def readTwoBytes(f):
    dat = f.read(2)
    return (ord(dat[0])<<8) | ord(dat[1])

def readByte(f):
    return ord(f.read(1))

def readDelta(f):
    ret = 0
    while True:
        v = readByte(f)
        ret = (ret << 7) | (v & 0x7F)
        if v<0x80:
            return ret        

def readHeaderChunk(f):
    dat = f.read(4)
    if dat!="MThd":
        raise Exception("Missing 'MThd' header") 
    en = readFourBytes(f)
    if en!=6:
        raise Exception("Expected header length to be 6 bytes but got "+str(en))
    return (readTwoBytes(f),readTwoBytes(f),readTwoBytes(f))

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
            pass
        elif com==9:
            nn = readByte(f)
            ve = readByte(f)
            e = MidiEvent(delta,chan,"NoteOn",[nn,ve])
            prev = e
            ret.append(e)
            continue
        elif com==10:
            pass
        elif com==11:
            cn = readByte(f)
            va = readByte(f)
            e = MidiEvent(delta,chan,"ControllerChange",[cn,va])
            prev = e
            ret.append(e)
            continue
        elif com==12:
            prg = readByte(f)
            MidiEvent(delta,chan,"ProgramChange",[prg])
            prev = e
            ret.append(e)
            continue
        elif com==13:
            pass
        elif com==14:
            pass
        elif com==15:
            pass        
        
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
            