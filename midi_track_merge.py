from midi_file import MIDIFile
from midi_events import ContinuationEvent

def merge_tracks(tracks):
    """Merge multiple midi tracks into a single track
    
    MIDI files usually contain multiple tracks that are to be played at the
    same time. This function pulls all the events from multiple tracks into 
    a single track with translated time deltas.
    
    Params:
      tracks (list): The separate MIDI tracks
      
    Returns:
      track: The single, combined MIDI track      
    """       
    tick_tracking = []
    for track in tracks:
        tick_tracking.append([track[0].delta,0,track])
        
    master_delta = 0
    ret = []
    
    while len(tick_tracking)>0:    # Tracks drop out as they complete
        event_added=False
        for tt in tick_tracking:     # Process track one at a time
            if tt[0]>0:  
                # Not time for this track's event. Just decrement the time.       
                tt[0] = tt[0]-1     
            else:
                while tt[0]==0: # Might be several events at this time
                    # Add this event to the master timeline
                    ne = tt[2][tt[1]].make_copy(master_delta)
                    if isinstance(ne,ContinuationEvent):
                        ne = ne.get_expanded_event()
                    ret.append(ne)
                    # Move the master delta to 0 (an event just happened)
                    master_delta = 0         
                    event_added=True           
                    # Move to the next event in the track, remove if none, add if delta is 0
                    tt[1] = tt[1] + 1 # Next event
                    if tt[1]>=len(tt[2]):
                        # Done with this track ... remove it and break out of loop
                        tick_tracking.remove(tt)
                        break
                    tt[0] = tt[2][tt[1]].delta 
        if not event_added:
            master_delta = master_delta + 1 # Nothing happened this tick
    
    return ret
