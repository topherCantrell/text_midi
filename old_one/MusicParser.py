import string

from midi.MidiEvents import MidiEvent
from midi import MidiTools

def pullDefines(lines):
    dfs = {}
    current = None
    for x in xrange(len(lines)):
        line = lines[x]
        if line.endswith("%"):
            nm = line[0:-1]
            current = []
            dfs[nm] = current
        else:
            if line.startswith("Track"):
                current = None
            else:
                if current!=None:
                    current.append(line)
    return dfs

def pullTracks(lines):
    tracks = {}
    current = None
    for x in xrange(len(lines)):
        line = lines[x]
        if line.startswith("Track"):
            nm = int(line[6:-1])
            current = []
            tracks[nm] = current
        else:
            if line.endswith("%") or line.startswith("Track"):
                current = None
            else:
                if current!=None:
                    current.append(line)   
    return tracks 

def combineUse(dat):
    ntr = []
    x = 0
    while x<len(dat):
        line = dat[x]
        if line.startswith("%"):
            if "(" in line:
                while not line.endswith(")"):
                    x = x + 1
                    line = line + dat[x]                    
        ntr.append(line)
        x=x+1
    return ntr

def processUses(lines,dfs):    
    changed = True
    while(changed):
        changed = False        
        for x in xrange(len(lines)):            
            line = lines[x]
            if not line.startswith("%"):
                continue
             
            changed = True  
            subs = {}
            name = line[1:]    
            if "(" in line:
                i = line.index("(")
                name = line[1:i]
                subSpec = line[i+1:-1].split(",")
                for ss in subSpec:
                    kv = ss.split("<-")
                    subs[kv[0].strip()] = kv[1].strip()  
                    
            df = list(dfs[name])
                
            rep = [] 
            for n in df:
                for (key,val) in subs.iteritems():
                    n = n.replace(key,val)
                rep.append(n)
                
            # Do the substitution in place
            del lines[x]
            for nl in rep:
                lines.insert(x,nl)
                x=x+1
                
NOTE_VALUES = {  # TODO: This is key of C             
               'C':0,
               'D':2,
               'E':4,
               'F':5,
               'G':7,
               'A':9,
               'B':11,               
               }
                
def processTrack(channel, track):
    global NOTE_VALUES
    ret = []
    lon = ""
    for line in track:
        if line.startswith("^"):
            continue
        lon = lon + " "+line
    lon = lon.replace("|","").strip()
    while "  " in lon:
        lon = lon.replace("  "," ")
    toks = lon.split(" ")
       
    ticksPerWhole = 480.0    
    noteOnPercent = 0.80 # TODO: configurable
    curLen = 1.0
    curOctave = 5    
    waitBefore = 0.0
    for tok in toks:            
        
        if tok.startswith("Patch_"):
            prg = int(tok[6:])
            pe  = MidiEvent(0,channel,"ProgramChange",[0xC0+channel,prg])
            ret.append(pe)
            continue
          
        if tok[0] in string.digits:
            # TODO: could be two digits like "16"
            curLen = ticksPerWhole / float(tok[0])
            tok = tok[1:]
            # TODO: could be multiple dots
            if tok[0] == ".":
                curLen = curLen + curLen/2.0
                tok = tok[1:]
                
        if tok[0] == 'R':
            waitBefore = waitBefore + curLen
            continue
                        
        noteVal = NOTE_VALUES[tok[0]]
        tok = tok[1:]
            
        # TODO: could be multiple accidentals
        if(len(tok)>0):
            if(tok[0]=='b'):
                noteVal = noteVal - 1
                tok = tok[1:]
            elif(tok[0]=='#'):
                noteVal = noteVal + 1
                tok = tok[1:]
        
        # TODO: could be multiple + and -
        if(len(tok)>0):
            if(tok[0] in string.digits):
                curOctave = int(tok[0])
                tok = tok[1:]
            elif tok[0]=='+':
                curOctave = curOctave + 1
                tok = tok[1:]
            elif tok[0]=='-':
                curOctave = curOctave - 1
                tok = tok[1:]
                
        if(len(tok)!=0):
            raise Exception("OOPS")
                
        noteVal = curOctave*12 + noteVal
        
        onTime = curLen * noteOnPercent
        offTime = curLen - onTime
        
        non  = MidiEvent(int(waitBefore),channel,"NoteOn",[0x90+channel,noteVal,128])
        noff = MidiEvent(int(onTime),channel,"NoteOff",[0x80+channel,noteVal,128])
        ret.append(non)
        ret.append(noff)
        
        #print str(waitBefore)+" NoteOn "+str(channel)+" "+str(noteVal)+" 128"
        #print str(onTime)+" NoteOff "+str(channel)+" "+str(noteVal)+" 128"
           
        waitBefore = offTime
            
    return ret                

def processMusic(filename):
    with open(filename) as f:
        rawLines = f.readlines()
        
    lines = []
    for x in xrange(len(rawLines)):
        line = rawLines[x]
        if ";" in line:
            i = line.index(";")
            line = line[0:i]
        line = line.strip()
        if len(line)>0:
            lines.append(line)
            
    lines = combineUse(lines)
            
    dfs = pullDefines(lines)
    tracks = pullTracks(lines)
    
    for track in tracks.values():
        processUses(track,dfs)
        
    ret = []
    for cnt in xrange(32):
        if cnt in tracks:
            track = processTrack(cnt,tracks[cnt])
            ret.append(track)    
       
    return ret

if __name__=="__main__":
        
    ret = processMusic('../TwelveDays.txt')
    MidiTools.printTracks(ret)     
            