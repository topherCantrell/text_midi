import sys
from midi_file import MIDIFile

"""Extract and print the data from a binary MIDI file"""

def print_midi_as_text(filename):
    """Prints the information from a MIDI file
    
    Params:
      filename (str): Name of the file      
    """
    midi = MIDIFile()
    midi.parse_file(filename)        
    print("NumTracks=%d Format=%d Division=%d" % (len(midi.tracks),midi.format,midi.divis))

    print_tracks(midi.tracks)    
        
def print_tracks(tracks):
    """Print the events in a list of tracks from a MIDI file
    
    Params:
        tracks (list): The list of tracks
    """
    tn = 0
    for track in tracks:
        print(""        )
        print("Track %d ; %d events" % (tn,len(track)))
        print_track(track)
        tn += 1
    
def print_track(track):
    """Print the events of a track from a MIDI file
    
    Params:
      track (list): the midi track      
    """        
    for e in track:
        print(str(e))

if __name__ == "__main__":    
    print_midi_as_text(sys.argv[1])