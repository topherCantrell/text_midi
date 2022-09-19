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
from midi_events import MetaEvent, SystemExclusiveEvent
from midi_events import MIDIChannelNoteEvent
from midi_events import MIDIChannelProgramChangeEvent
from midi_events import MIDIChannelControlChangeEvent
from midi_events import MIDIChannelPolyphonicKeyPressureEvent
from midi_events import MIDIChannelRunningStatusEvent

def file_to_midi(filename):
    tracks = []
    previous = None
    with open(filename,'r') as f:
        for line in f:
            if line.startswith('NumTracks'):
                infos = line.split()
                info = {}
                for s in infos:
                    key,value = s.split('=')
                    info[key] = int(value)        
                continue
            i = line.find(';')
            if i>=0:
                line = line[0:i]
            line = line.strip()
            if not line:
                continue
            if line.startswith('Track '):
                tracks.append([])
                continue            
                
            line = line.split()
            delta = int(line[0])
            if line[1]=='MetaEvent':
                data = []
                for d in line[3:]:
                    data.append(int(d))
                evt = MetaEvent(delta,int(line[2]),data)
                tracks[-1].append(evt)
            elif line[1]=='ProgramChange':
                evt = MIDIChannelProgramChangeEvent(delta,int(line[2]),int(line[3]))
                tracks[-1].append(evt)
                previous = evt
            elif line[1]=='ControlChange':
                evt = MIDIChannelControlChangeEvent(delta,int(line[2]),int(line[3]),int(line[4]))
                tracks[-1].append(evt)
                previous = evt
            elif line[1]=='NoteOn':
                evt = MIDIChannelNoteEvent(delta,int(line[2]),True,int(line[3]),int(line[4]))
                tracks[-1].append(evt)
                previous = evt
            elif line[1]=='NoteOff':
                evt = MIDIChannelNoteEvent(delta,int(line[2]),False,int(line[3]),int(line[4]))
                tracks[-1].append(evt)
                previous = evt
            elif line[1]=='RunningStatus':
                data = []
                for d in line[2:]:
                    data.append(int(d))
                evt = MIDIChannelRunningStatusEvent(delta,previous,data)
                tracks[-1].append(evt)
            else:
                raise Exception(f'Invalid event "{line}"')
    ret = MIDIFile()
    ret.tracks = tracks
    ret.format = int(info['Format'])
    ret.divis = int(info['Division'])
    if len(tracks)!= int(info['NumTracks']):
        raise Exception('Incorrect number of tracks')

    return ret

if __name__ == '__main__':
    midi = file_to_midi(sys.argv[1])
    midi.write_file(sys.argv[2])
