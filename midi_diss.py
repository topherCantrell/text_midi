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
