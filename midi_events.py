
class MetaEvent:
    """MIDI Meta Events
    
    """
    
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
        
        Args:
          new_delta (float): the new tick delta
          
        Returns:
          MetaEvent: the new MetaEvent
        """
        
        ret = MetaEvent(new_delta,self.meta_type,self.meta_data)
        return ret
        
    def __str__(self):
        """Returns a text representation of the MetaEvent
        
        TODO: use the __str() name
        
        Returns:
          str: String representation
          
        """
        
        ds = ''
        com = ''
        if self.meta_type==0x51:
            tempo = (self.meta_data[0]<<16) | (self.meta_data[1]<<8) | (self.meta_data[2])
            com = " ; tempo="+str(tempo)
        for x in self.meta_data:
            ds = ds + " "+str(x)
        return "# %5d   MetaEvent %3d    %s%s" % (self.delta,self.meta_type,ds,com)
        
class MIDIEvent:
    """MIDI Channel Events
    
    """
    
    def __init__(self, delta, channel, event_type, data):
        self.channel = channel
        self.delta = delta
        self.event_type = event_type
        self.data = data        
        
    def make_copy(self,new_delta):
        ret = MIDIEvent(new_delta,self.channel,self.event_type,self.data)
        return ret
        
    def __str__(self):
        ds = " ".join(str(x) for x in self.data)
        return"# %5d   %s:%d %s" %(self.delta,self.event_type,self.channel,ds) # channel, eventType, data
    
    def get_midi_bytes(self):
        ds = "".join(chr(x) for x in self.data)
        return ds       
        
class ContinuationEvent:
    """MIDI Continuation Events
    
    MIDI allows the same events on the same channel to skip the command byte. Data bytes
    simply injected behind the data bytes of the last command.
    
    """
    def __init__(self, delta, previous_event, data):
        self.delta = delta
        self.previous_event = previous_event
        self.data = data
        
    def make_copy(self,new_delta):
        ret = ContinuationEvent(new_delta,self.previous_event,self.data)
        return ret
    
    def get_expanded_event(self):
        dat = self.data
        dat.insert(0,self.previous_event.data[0])
        ret = MIDIEvent(self.delta,self.previous_event.channel,self.previous_event.event_type,self.data)        
        return ret        
        
    def __str__(self):
        ds = " ".join(str(x) for x in self.data)
        return "# %5d   %s ; %s:%d" % (self.delta,ds,self.previous_event.event_type,self.previous_event.channel)
