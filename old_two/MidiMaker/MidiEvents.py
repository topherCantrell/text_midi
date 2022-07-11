
class MetaEvent:
    def __init__(self, delta, metaType, metaData):
        self.delta = delta
        self.metaType = metaType
        self.metaData = metaData       
        
    def makeCopy(self,newDelta):
        ret = MetaEvent(newDelta,self.metaType,self.metaData)
        return ret
        
    def getText(self):
        ds = ""
        com = ""
        if self.metaType==0x51:
            tempo = (ord(self.metaData[0])<<16) | (ord(self.metaData[1])<<8) | (ord(self.metaData[2]))
            com = " ; tempo="+str(tempo)
        for x in self.metaData:
            ds = ds + " "+str(ord(x))
        return "# %5d   MetaEvent %3d    %s%s" % (self.delta,self.metaType,ds,com)
        
class MidiEvent:
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
        
class ContinuationEvent:
    def __init__(self, delta, previousEvent, data):
        self.delta = delta
        self.previousEvent = previousEvent
        self.data = data
        
    def makeCopy(self,newDelta):
        ret = ContinuationEvent(newDelta,self.previousEvent,self.data)
        return ret
    
    def getExpandedEvent(self):
        ne = MidiEvent(self.delta,self.previousEvent.channel,self.previousEvent.eventType,self.data)        
        return ne
        
        
    def getText(self):
        ds = " ".join(str(x) for x in self.data)
        return "# %5d   %s ; %s:%d" % (self.delta,ds,self.previousEvent.eventType,self.previousEvent.channel)
