
import MidiFile
from MidiEvents import ContinuationEvent

def mergeTracks(tracks):
    
    tickTracking = []
    for track in tracks:
        tickTracking.append([track[0].delta,0,track])
        
    masterDelta = 0
    ret = []
    
    while len(tickTracking)>0:    # Tracks drop out as they complete
        eventAdded=False
        for tt in tickTracking:     # Process track one at a time
            if tt[0]>0:  
                # Not time for this track's event. Just decrement the time.       
                tt[0] = tt[0]-1     
            else:
                while tt[0]==0: # Might be several events at this time
                    # Add this event to the master timeline
                    ne = tt[2][tt[1]].makeCopy(masterDelta)
                    ret.append(ne)
                    # Move the master delta to 0 (an event just happened)
                    masterDelta = 0         
                    eventAdded=True           
                    # Move to the next event in the track, remove if none, add if delta is 0
                    tt[1] = tt[1] + 1 # Next event
                    if tt[1]>=len(tt[2]):
                        # Done with this track ... remove it and break out of loop
                        tickTracking.remove(tt)
                        break
                    tt[0] = tt[2][tt[1]].delta 
        if not eventAdded:
            masterDelta = masterDelta + 1 # Nothing happened this tick
    
    return ret

(time,tracks) = MidiFile.parseFile("score.mid")
mt = mergeTracks(tracks)
for e in mt:
    if isinstance(e,ContinuationEvent):
        e = e.getExpandedEvent()
    print e.getText()

"""
    
print "; numTracks=%d  time=%d" % (len(tracks),time)
print '\n\n'

tn = 0
for track in tracks:        
    print "Track %d ; %d events" % (tn,len(track))
    for e in track:
        print e.getText()
    print '\n\n'
    
   """ 