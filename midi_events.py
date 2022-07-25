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

"""
All the different (supported) MIDI event types.
"""

class MetaEvent:
    """MIDI Meta Events

    Meta events have a type and a list of data bytes.
    
    """

    # Some well-known meta events (add more as needed)
    TYPE_DESC = {
        0x00: 'Sequence number',
        0x01: 'Text event',
        0x02: 'Copyright notice (text)',
        0x03: 'Sequence or track name (text)',
        0x04: 'Instrument name (text)',
        0x05: 'Lyric text',
        0x06: 'Marker text',
        0x07: 'Cue point',
        0x08: 'Program name (text)',
        0x0A: '?Author? (text)',
        0x20: 'MIDI channel prefix assignment',
        0x2F: 'END OF TRACK', # Required at the end of every track
        0x51: 'Tempo setting',
        0x54: 'SMPTE offset',
        0x58: 'Time signature',
        0x59: 'Key signature',
        0x7F: 'Sequencer specific event',
    }
    
    def __init__(self, delta, meta_type, meta_data):
        """Create a new MetaEvent
        
        Args:
          delta (float):      ticks to wait before event
          meta_type (int):    the type-byte of the meta event 
          meta_data (int []): the data bytes of the meta event        

        """        
        self.delta = delta
        self.meta_type = meta_type
        self.meta_data = meta_data       
        
    def make_copy(self,new_delta):
        """Make a copy of the MetaEvent but with a new time delta

        This is used by the track-merger to move events around in time.
        
        Args:
          new_delta (float): the new tick delta
          
        Returns:
          MetaEvent: the new MetaEvent

        """        
        ret = MetaEvent(new_delta,self.meta_type,self.meta_data)
        return ret
        
    def __str__(self):
        """Returns a text representation of the MetaEvent

        This is the midi-assembly format.
                
        Returns:
          str: String representation          

        """        
        ds = ''
        com = ''

        if self.meta_type in MetaEvent.TYPE_DESC:
            com = ' ; '+MetaEvent.TYPE_DESC[self.meta_type]
            if 'text' in com.lower():
                com += ' "'
                for x in self.meta_data:
                    if x>=32 and x<128:
                        com += chr(x)
                com += '"'        
        
        for x in self.meta_data:
            ds = ds + "%3d " % x
        return "%-7d MetaEvent     %3d %s%s" % (self.delta,self.meta_type,ds,com)

class SystemExclusiveEvent:
    """A message intended for a specific piece of hardware
    """

    def __init__(self,delta,data):
        self.delta = delta
        self.data = data

    def make_copy(self,new_delta):
        return SystemExclusiveEvent(new_delta,self.data)

    def __str__(self):
        ds = '' 
        for x in self.data:
            ds = ds + " "+str(x)
        return "%-7d SysExEvent    %s" % (self.delta,ds)


class MIDIChannelNoteEvent:
    """MIDI Channel Note Event

    A note being pressed (on) or released (off) with a velocity value either way.

    For example:
      * DELTA NoteOn CH NOTE VELOCITY
      * DELTA NoteOff CH NOTE VELOCITY
    
    """    
    
    def __init__(self, delta, channel, note_on, note, velocity):
        self.channel = channel
        self.delta = delta
        self.note_on = note_on
        self.note = note
        self.velocity = velocity
        
    def make_copy(self,new_delta):
        ret = MIDIChannelNoteEvent(new_delta,self.channel,self.note_on,self.note,self.velocity)
        return ret
        
    def __str__(self):
        if self.note_on:
            event_type = 'NoteOn        '
        else:
            event_type = 'NoteOff       '
        return "%-7d %s %2d %3d %3d" %(self.delta,event_type,self.channel,self.note,self.velocity)

class MIDIChannelProgramChangeEvent:
    """MIDI Channel Program Change Event

    This usually means assigning a different instrument to the channel.

    For example:
      * DELTA ProgramChange CH VALUE

    """

    def __init__(self, delta, channel, value):
        self.channel = channel
        self.delta = delta
        self.value = value        
        
    def make_copy(self,new_delta):
        ret = MIDIChannelProgramChangeEvent(new_delta,self.channel,self.value)
        return ret
        
    def __str__(self):        
        return "%-7d ProgramChange  %2d %3d" %(self.delta, 45, self.value)

class MIDIChannelControlChangeEvent:
    """MIDI Channel Control Change Event

    This usually means devices like pedals and levers have changed.
    Controllers 120-127 are reserved as "channel mode messages" (same
    data format).

    For example:
      * DELTA ControlChange CH VALUE

    """

    def __init__(self, delta, channel, controller, value):
        self.channel = channel
        self.controller = controller
        self.delta = delta
        self.value = value        
        
    def make_copy(self,new_delta):
        ret = MIDIChannelControlChangeEvent(new_delta,self.channel,self.controller, self.value)
        return ret
        
    def __str__(self):        
        return "%-7d ControlChange  %2d %3d %3d" %(self.delta, self.channel,self.controller,self.value)
    
class MIDIChannelPolyphonicKeyPressureEvent:
    """MIDI Channel Polyphonic Key Pressure Event (Aftertouch)   

    For example:
      * DELTA PolyphonicKeyPressure CH NOTE VALUE

    """

    def __init__(self, delta, channel, note, value):
        self.channel = channel
        self.note = note
        self.delta = delta
        self.value = value        
        
    def make_copy(self,new_delta):
        ret = MIDIChannelPolyphonicKeyPressureEvent(new_delta,self.channel,self.note, self.value)
        return ret
        
    def __str__(self):        
        return "%-7d PolyKeyPress  %2d %3d %3d" %(self.delta, self.channel,self.note,self.value)

           
class MIDIChannelRunningStatusEvent:
    """MIDI Channel Running Status Event
    
    MIDI allows the same events on the same channel to skip the command byte. Data bytes
    simply injected behind the data bytes of the last command.
    
    """
    def __init__(self, delta, previous_event, data):
        self.delta = delta
        self.previous_event = previous_event
        self.data = data
        
    def make_copy(self,new_delta):
        ret = MIDIChannelRunningStatusEvent(new_delta,self.previous_event,self.data)
        return ret        
        
    def __str__(self):
        ds = " ".join("%3d" % (x,) for x in self.data)
        return "%-7d RunningStatus %s" % (self.delta,ds)
