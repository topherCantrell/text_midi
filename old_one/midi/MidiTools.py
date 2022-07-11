import MidiFile
from MidiEvents import ContinuationEvent

def mergeTracks(tracks):
    """Merge multiple midi tracks into a single track
    
    MIDI files usually contain multiple tracks that are to be played at the
    same time. This function pulls all the events into a single track with
    translated time deltas.
    
    Args:
      tracks (list): The separate MIDI tracks
      
    Returns:
      track: The single, combined MIDI track
      
    """   
    
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
                    if isinstance(ne,ContinuationEvent):
                        ne = ne.getExpandedEvent()
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

def printMidiAsText(filename):
    """Print the tracks and events in a MIDI file
    
    Args:
      filename (str): Name of the file
      
    """
    
    (time,tracks) = MidiFile.parseFile(filename)
    print "; numTracks=%d  time=%d" % (len(tracks),time)
    print '\n\n'

    printTrcks(tracks)    
        
def printTracks(tracks):
    tn = 0
    for track in tracks:
        print ""        
        print "Track %d ; %d events" % (tn,len(track))
        printTrack(track)
        tn += 1
    
def printTrack(track):
    """Prints info about a single track
    
    Args:
      track (list): the midi track
      
    """
        
    for e in track:
        print e.getText()

