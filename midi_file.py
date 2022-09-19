"""
MIT License

Copyright (c) 2022 Chris Cantrell

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from midi_events import MetaEvent, SystemExclusiveEvent
from midi_events import MIDIChannelNoteEvent
from midi_events import MIDIChannelProgramChangeEvent
from midi_events import MIDIChannelControlChangeEvent
from midi_events import MIDIChannelPolyphonicKeyPressureEvent
from midi_events import MIDIChannelRunningStatusEvent

class MIDIDataCursor:

    def __init__(self,data=None,pos=0):
        if data:
            self.data = data
        else:
            self.data = []
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

    def write_bytes(self,data):
        self.data.extend(data)

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
            self.write_byte(d)
        

class MIDIFile:

    """
    MIDI file header:

    "MThd" + 0006 + FF + NN + DD
      - FF Format (01 for multiple-track-file)
      - NN number of tracks that follow
      - DD time division (96 means 96 ticks per beat)

    "MTrk" + SSSS + EVENT+EVENT+EVENT...

    Event:
    <v_time> + <event>    
    """

    def __init__(self):                
        self.format = None
        self.divis = None        
        self.tracks = None

    def write_file(self,filename):

        cursor = MIDIDataCursor()
        cursor.write(b'MThd')

        cursor.write_four_bytes(6) # Length of the header record (always 6 bytes)

        cursor.write_two_bytes(self.format) # How to interpret the tracks (likely a 01 for multi-track-song)
        cursor.write_two_bytes(len(self.tracks))
        cursor.write_two_bytes(self.divis)

        for track in self.tracks:
            track_data = MIDIDataCursor()
            for event in track:

                # Every event starts with a delta
                track_data.write_delta(event.delta)

                if isinstance(event,MetaEvent):
                    track_data.write_byte(0xFF)
                    track_data.write_byte(event.meta_type)
                    track_data.write_delta(len(event.meta_data))
                    track_data.write_bytes(event.meta_data)

                elif isinstance(event,MIDIChannelProgramChangeEvent):
                    track_data.write_byte(0xC0 | event.channel)                    
                    track_data.write_byte(event.value)

                elif isinstance(event,MIDIChannelControlChangeEvent):
                    track_data.write_byte(0xB0 | event.channel)
                    track_data.write_byte(event.controller)
                    track_data.write_byte(event.value)

                elif isinstance(event,MIDIChannelRunningStatusEvent):
                    track_data.write_bytes(event.data)                                        

                elif isinstance(event,MIDIChannelNoteEvent):
                    if event.note_on:
                        track_data.write_byte(0x90 | event.channel)
                    else:
                        track_data.write_byte(0x80 | event.channel)
                    track_data.write_byte(event.note)
                    track_data.write_byte(event.velocity)

                else:                                        
                    raise NotImplementedError(event)                               

            cursor.write(b'MTrk')
            cursor.write_four_bytes(len(track_data.data))
            cursor.write_bytes(track_data.data)            

        with open(filename,'wb') as f:
            f.write(bytes(cursor.data))
            f.flush()

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
        
        ret = [] # The events of this track
        
        # Check the header
        dat = cursor.read(4)
        if dat!=b'MTrk':
            raise Exception("Missing 'MTrk' header")
        trackSize = cursor.read_four_bytes()    
                
        end_of_track = cursor.pos+trackSize

        # Information about the last command for the "running status" feature        
        previous = None
        previous_size = 0

        while cursor.pos<end_of_track:       
                        
            # Evert event starts with a var-length delta
            delta = cursor.read_delta()        

            d = cursor.read_byte()

            # MIDI lets you skip the status byte of the event and use the last given one.
            # This makes for a shorter file without all the repeated "note on" and "note off".
            # If the upper bit is NOT set, then this uses the last event type.
            if d<128: # This is data ... running status shortcut
                if not isinstance(previous,MIDIChannelNoteEvent) and not isinstance(previous,MIDIChannelControlChangeEvent):
                    # I've only seen these two kinds of continuations, but there might be others. Add
                    # them if you see them.
                    raise NotImplemented(f'UNSUPPORTED PREVIOUS {type(previous)}')
                data = [d] # The first byte counts as data
                for _ in range(previous_size-1):
                    data.append(cursor.read_byte())                
                evt = MIDIChannelRunningStatusEvent(delta,previous,data)
                ret.append(evt) 
                continue
        
            # FF -- META events            
            if(d==0xFF):
                meta_type = cursor.read_byte()
                meta_len = cursor.read_delta()
                meta_data = cursor.read(meta_len)                
                evt = MetaEvent(delta,meta_type,meta_data)
                ret.append(evt)                
                continue

            command = d>>4 # Upper 4 bits

            # Fx -- System Exclusive events
            if command==15: # (but wasn't 0xFF) System Exclusive
                if d==0b11110000 or d==0b11110010 or d==0b11110011:
                    # There are others. Add them as you see them. Some have
                    # multiple data bytes.
                    raise NotImplemented(d)
                evt = SystemExclusiveEvent(delta,[d])                
                ret.append(evt)
                continue
            
            # This must be a channel event
                        
            channel = d&0xF # Lower 4 bits
                
            if command==8: # Note Off Event
                note = cursor.read_byte()
                velocity = cursor.read_byte()
                evt = MIDIChannelNoteEvent(delta,channel,False,note,velocity)
                previous = evt
                previous_size = 2
                ret.append(evt)                          
                
            elif command==9: # Note On Event
                # MIDI allows NoteOn-velocity-0 to mean NoteOff
                note = cursor.read_byte()
                velocity = cursor.read_byte()
                evt = MIDIChannelNoteEvent(delta,channel,True,note,velocity)
                previous = evt
                previous_size = 2
                ret.append(evt)                           
                
            elif command==10: # Polyphonic Key Pressure
                note = cursor.read_byte()
                value = cursor.read_byte()
                evt = MIDIChannelPolyphonicKeyPressureEvent(delta,channel,note,value)
                previous = evt
                previous_size = 2
                ret.append(evt)                

            elif command==11: # Control Change
                cntr = cursor.read_byte()
                value = cursor.read_byte()
                evt = MIDIChannelControlChangeEvent(delta,channel,cntr,value)
                previous = evt
                previous_size = 2
                ret.append(evt)                
                
            elif command==12: # Program Change
                program = cursor.read_byte()
                evt = MIDIChannelProgramChangeEvent(delta,channel,program)
                previous = evt
                ret.append(evt)                
                
            elif command==13: # Channel Pressure
                # Add if you need it.
                raise NotImplemented()

            elif command==14: # Pitch Bend Change
                # Add if you need it.
                raise NotImplemented()

            elif command==15: # (but wasn't 0xFF) System Exclusive
                if d==0b11110000 or d==0b11110010 or d==0b11110011:
                    raise NotImplemented()
                evt = SystemExclusiveEvent(delta,[d])                
                ret.append(evt)
                #print(delta,hex(old_pos),evt)

            else:
                # It isn't really possible to get here. We checked all
                # possibilities. But just in case.
                raise Exception('Unknown command '+str(command))                    
        
        if not isinstance(ret[-1],MetaEvent) or ret[-1].meta_type!=0x2F:
            raise Exception('Missing END OF TRACK Meta Event')

        return ret
