from midi_events import MetaEvent, ContinuationEvent, MIDIEvent

class MIDIDataCursor:

    def __init__(self,data,pos):
        self.data = data
        self.pos = pos

    def read(self,size):
        ret = bytes(self.data[self.pos:self.pos+size])
        self.pos += size
        return ret

    def write(self,data):
        self.data = self.data + list(data)
    
    def read_byte(self):
        ret = self.data[self.pos]
        self.pos += 1
        return ret

    def write_byte(self,value):
        self.data.append(value)

    def read_two_bytes(self):
        return (self.read_byte()<<8) | self.read_byte()    

    def write_two_bytes(self,value):
        a = (value>>8) & 0xFF
        b = value & 0xFF
        self.write_byte(a)
        self.write_byte(b)

    def read_four_bytes(self):
        return (self.read_two_bytes()<<16) | self.read_two_bytes()

    def write_four_bytes(self,value):
        a = (value>>16) & 0xFFFF
        b = value & 0xFFFF
        self.write_two_bytes(a)
        self.write_two_bytes(b)

    def read_delta(self):
        ret = 0
        while True:
            v = self.read_byte()
            ret = (ret << 7) | (v & 0x7F)
            if v<0x80:
                return ret

    def write_delta(self,delta):
        buf = []
        while True:
            if delta<0x80:
                buf.append(delta)
                break
            buf.append(delta&0x7F)
            delta = delta >> 7
        for i in range(len(buf)-1,-1,-1):
            d = buf[i]
            if i!=0:
                d = d | 0x80
            self.write_byte(buf[i])
        

class MIDIFile:

    def __init__(self):                
        self.format = None
        self.divis = None        
        self.tracks = None

    def build_file(self,format,divis,tracks):
        self.format = format
        self.divis = divis
        self.tracks = tracks        

    def parse_file(self,filename):
        # Load the entire file as a list of integers
        with open(filename,'rb') as f:
            data = list(f.read())        

        cursor = MIDIDataCursor(data,0)
        
        self.format,num_tracks,self.divis = self.read_header_chunk(cursor)

        self.tracks = []    
        for _ in range(num_tracks):    
            events = self.read_track_chunk(cursor)
            self.tracks.append(events)    
        
    def read_header_chunk(self,cursor):
        dat = cursor.read(4)
        if dat!=b'MThd':
            raise Exception("Missing 'MThd' header") 
        en = cursor.read_four_bytes()
        if en!=6:
            raise Exception("Expected header length to be 6 bytes but got "+str(en))
        format = cursor.read_two_bytes()
        numTracks = cursor.read_two_bytes()
        divis = cursor.read_two_bytes()
        return format,numTracks,divis

    def read_track_chunk(self,cursor):
        
        ret = []
        
        dat = cursor.read(4)
        if dat!=b'MTrk':
            raise Exception("Missing 'MTrk' header")
        trackSize = cursor.read_four_bytes()    
        
        end_of_track = cursor.pos+trackSize
        
        previous = None

        while cursor.pos<end_of_track:        
            delta = cursor.read_delta()        
        
            # Handle META events

            d = cursor.read_byte()
            if(d==0xFF):
                meta_type = cursor.read_byte()
                meta_len = cursor.read_delta()
                meta_data = cursor.read(meta_len)                
                e = MetaEvent(delta,meta_type,meta_data)
                ret.append(e)
                continue
            
            # This is a channel event

            command = d>>4
            channel = d&0xF
            
            if command<8: # Continuation Event
                data = cursor.read_byte()
                evt = ContinuationEvent(delta,previous,[d,data])
                ret.append(evt)            
                
            elif command==8: # Note Off Event
                note = cursor.read_byte()
                velocity = cursor.read_byte()
                evt = MIDIEvent(delta,channel,"NoteOff",[d,note,velocity])
                previous = evt
                ret.append(evt)
                
            elif command==9: # Note On Event
                # MIDI allows NoteOn-velocity-0 to mean NoteOff
                note = cursor.read_byte()
                velocity = cursor.read_byte()
                evt = MIDIEvent(delta,channel,"NoteOn",[d,note,velocity])
                previous = evt
                ret.append(evt)
                
            elif command==10: # Polyphonic Key Pressure
                raise NotImplemented()

            elif command==11: # Control Change
                controller = cursor.read_byte()
                value = cursor.read_byte()
                evt = MIDIEvent(delta,channel,"ControllerChange",[d,controller,value])
                previous = evt
                ret.append(evt)
                
            elif command==12: # Program Change
                program = cursor.read_byte()
                evt = MIDIEvent(delta,channel,"ProgramChange",[d,program])
                previous = evt
                ret.append(evt)
                
            elif command==13: # Channel Pressure
                raise NotImplemented()

            elif command==14: # Pitch Bend Change
                raise NotImplemented()

            elif command==15: # System Exclusive
                raise NotImplemented()                                
        
        return ret
    

    def write_file(self,filename):
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
        raise NotImplemented()
