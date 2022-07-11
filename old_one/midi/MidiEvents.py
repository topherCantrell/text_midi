
class MetaEvent:
    """MIDI Meta Events
    
    """
    
    def __init__(self, delta, metaType, metaData):
        """Create a new MetaEvent
        
        Args:
          delta (float):     ticks to wait before event
          metaType (int):    the type-byte of the meta event 
          metaData (int []): the data bytes of the meta event
          
        """
        
        self.delta = delta
        self.metaType = metaType
        self.metaData = metaData       
        
    def makeCopy(self,newDelta):
        """Make a copy of the MetaEvent but with a new time delta
        
        Args:
          newDelta (float): the new tick delta
          
        Returns:
          MetaEvent: the new MetaEvent
        """
        
        ret = MetaEvent(newDelta,self.metaType,self.metaData)
        return ret
        
    def getText(self):
        """Returns a text representation of the MetaEvent
        
        TODO: use the __str() name
        
        Returns:
          str: String representation
          
        """
        
        ds = ""
        com = ""
        if self.metaType==0x51:
            tempo = (ord(self.metaData[0])<<16) | (ord(self.metaData[1])<<8) | (ord(self.metaData[2]))
            com = " ; tempo="+str(tempo)
        for x in self.metaData:
            ds = ds + " "+str(ord(x))
        return "# %5d   MetaEvent %3d    %s%s" % (self.delta,self.metaType,ds,com)
        
class MidiEvent:
    """MIDI Channel Events
    
    """
    
    def __init__(self, delta, channel, eventType, data):
        self.channel = channel
        self.delta = delta
        self.eventType = eventType
        self.data = data        
        
    def makeCopy(self,newDelta):
        ret = MidiEvent(newDelta,self.channel,self.eventType,self.data)
        return ret
        
    def getText(self):
        ds = " ".join(str(x) for x in self.data)
        return"# %5d   %s:%d %s" %(self.delta,self.eventType,self.channel,ds) # channel, eventType, data
    
    def getMidiBytes(self):
        ds = "".join(chr(x) for x in self.data)
        return ds       
        
class ContinuationEvent:
    """MIDI Continuation Events
    
    MIDI allows the same events on the same channel to skip the command byte. Data bytes
    simply injected behind the data bytes of the last command.
    
    """
    def __init__(self, delta, previousEvent, data):
        self.delta = delta
        self.previousEvent = previousEvent
        self.data = data
        
    def makeCopy(self,newDelta):
        ret = ContinuationEvent(newDelta,self.previousEvent,self.data)
        return ret
    
    def getExpandedEvent(self):
        dat = self.data
        dat.insert(0,self.previousEvent.data[0])
        ne = MidiEvent(self.delta,self.previousEvent.channel,self.previousEvent.eventType,self.data)        
        return ne        
        
    def getText(self):
        ds = " ".join(str(x) for x in self.data)
        return "# %5d   %s ; %s:%d" % (self.delta,ds,self.previousEvent.eventType,self.previousEvent.channel)
