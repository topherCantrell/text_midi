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

import string
import sys

from midi_events import MetaEvent, SystemExclusiveEvent
from midi_events import MIDIChannelNoteEvent
from midi_events import MIDIChannelProgramChangeEvent
from midi_events import MIDIChannelControlChangeEvent
from midi_events import MIDIChannelPolyphonicKeyPressureEvent
from midi_events import MIDIChannelRunningStatusEvent

#import midi_track_merge
import midi_diss
from midi_file import MIDIFile

def pull_tracks(lines):
    """Pull the music tracks from the list of lines.

    Tracks are of the form "Track X:", where X is the track name. All the
    music that follows the track-header (up to the next track) is
    part of the track.
    """
    tracks = {}
    current = None
    for line in lines:        
        if line['text'].startswith("Track"):
            nm = line['text'][6:]
            current = []
            tracks[nm] = current
        else:
            if current is not None:
                current.append(line)   
    return tracks 

def parse_note(text,defaults,err_text=None):

    # For errors
    if err_text is None:
        err_text = text

    # For example
    # >4.d~G#+:E#3:C#+
    
    # Separate out any secondary parallel notes
    par_notes = text.split(':')
    text = par_notes.pop(0)

    # Find the note name. It is required. CDEFGAB and R.
    fnd = False
    for i in range(len(text)):
        if text[i] in 'CDEFGABR':
            fnd = True
            break
    if not fnd:
        raise Exception('Note name is required in "'+err_text+'"')
    note_left = text[0:i]
    note_name = text[i]
    note_right = text[i+1:]

    # Accents are at the very beginning. Just one. ">.-^". They do not
    # default into the next note.
    note_accent = ""
    if note_left:                
        if note_left[0] in '>.-^':
            note_accent = note_left[0]
            note_left = note_left[1:]

    # Tie marks are at the very end of the note length. Just one "~". They
    # do not default into the next note.
    note_tie = False
    if note_left:
        if note_left[-1] == '~':
            note_tie = True
            note_left = note_left[:-1]

    # Note length is a number (multiple digits) followed by one or more dots.
    # The very end can be "t" for tuplet or "d" for duplet. Dots and "td" MUST
    # follow a note length number.
    note_len = ''
    note_dots = 0 
    note_plet = None
    while note_left and note_left[0] in '0123456789':
        note_len += note_left[0]
        note_left = note_left[1:]    
    if note_left and note_left[-1] in 'td':
        note_plet = note_left[-1]
        note_left = note_left[:-1]       
    while note_left and note_left[-1]=='.':
        note_dots += 1
        note_left = note_left[:-1]
    if note_plet or note_dots:
        if not note_len:
            raise Exception('Numeric length must also be given in "'+err_text+'"')

    # That's all we know about. Anything else to the left of the note name is invalid.
    if note_left:
        raise Exception('Invalid syntax left of note name "'+err_text+'"')

    # If a length was given then change the defaults
    # Otherwise, use the defaults
    if note_len:
        note_len = int(note_len)
        defaults['note_len'] = note_len        
        defaults['note_dots'] = note_dots
        defaults['note_plet'] = note_plet
    else:
        note_len = defaults['note_len']
        note_dots = defaults['note_dots']
        note_plet = defaults['note_plet']

    # At the moment, we don't support key signatures or persisting accidentals
    # through the measure. There is no need for a "natural" marking currently. 
    # There is no need for more than one sharp "#" or flat "b" marking on a note
    # currently.
    note_accidental = None
    if note_right:
        if note_right[0] in '#bn':
            note_accidental = note_right[0]
            note_right = note_right[1:]    

    # Octaves are on the end. They can be absolute numbers (multi digits) or they
    # can be multiple "+" or "-" to adjust the current octave. Either way, the
    # current ocatave becomes the new default octave.

    note_octave = ''
    while note_right and note_right[0] in '0123456789':
        note_octave += note_right[0]
        note_right = note_right[1:]
    if note_octave == '':
        note_octave = defaults['note_octave']
    else:
        note_octave = int(note_octave)
    while note_right and note_right[0] in '+-':
        octave_offset = note_right[0]
        note_right = note_right[1:]
        if octave_offset=='+':
            note_octave += 1
        else:
            note_octave -= 1

    defaults['note_octave'] = note_octave

    if note_right:
        raise Exception('Invalid syntax right of note name "'+err_text+'"')

    # Parallel notes are only note name (not rest), accidentals, and octave
    note_parallels = []
    for par in par_notes:               
        if not par or par[0] not in 'CDEFGAB':
            raise Exception('Invalid parallel note "'+par+'" in "'+err_text+'"')
        note_parallels.append(parse_note(par,defaults))        

    return {        
        # These values can carry between notes
        'note_len':note_len,        
        'note_dots':note_dots,
        'note_plet':note_plet,
        'note_octave':note_octave,
        # These values are not carried between notes
        'note_accent':note_accent,
        'note_tie':note_tie,        
        'note_name':note_name,
        'note_accidental':note_accidental,        
        'note_parallels':note_parallels,
    }

NOTE_VALUES = { # offsets within an octave             
               'C':0,
               'D':2,
               'E':4,
               'F':5,
               'G':7,
               'A':9,
               'B':11,               
               }

def get_midi_note_number(info):
    """Combine octave, note-name, and accidentals to get the midi note number

    Midi octaves go from -1 through 9. Midi note 0 is C-1. Midi note 12 is C0.
    Midi note 120 is C9. Our input system doesn't support negative numbers, but 
    you can specify octave "-1" with "0-".
    """
    octave = info['note_octave'] + 1
    ret = octave * 12 + NOTE_VALUES[info['note_name']]
    if info['note_accidental'] == '#':
        ret += 1
    elif info['note_accidental'] == 'b':
        ret -= 1
    return ret

def process_note(info,defaults,wait_before,events):
    # It is all about volume (velocity) and duration. The volume is given on
    # the NoteOn event. The duration is the distance between NoteOn and NoteOff.   

    # TODO handle ties

    bl = info['note_len']
    if info['note_plet'] == 't':
        bl = int(bl * 3 / 2)
    elif info['note_plet'] == 'd':
        bl = int(bl * 2 / 3)
    note_len = defaults['ticksPerWhole'] / bl

    # TODO handle multiple dots
    if info['note_dots']:
        note_len = note_len + note_len/2

    # TODO apply accents
    # TODO caller needs to keep up with increase/decrease volume over time
    velocity = int(defaults['volume']*127)

    # Number of ticks the note is on and off
    # TODO apply staccato, etc
    if info['note_name']=='R':
        # This is a rest ... just accumulate the entire note time
        return int(note_len) + wait_before        
    len_on = int(note_len * defaults['noteOnPercent'])
    len_off = int(note_len - len_on)

    # All notes on
    for ni in [info] + info['note_parallels']:
        note = get_midi_note_number(ni)
        events.append(MIDIChannelNoteEvent(wait_before,defaults['channel'],True,note,velocity))
        wait_before = 0     
    # All notes off
    for ni in [info] + info['note_parallels']:
        note = get_midi_note_number(ni)
        events.append(MIDIChannelNoteEvent(len_on,defaults['channel'],False,note,0))
        len_on = 0
    return len_off

def process_track(name,track):    
    ret = [] # List of midi events

    note_defaults = {   
        'channel' : 0,            # Can be changed per-track
        'tempo'   : 120,          # By default, midi is 120 beats (quarter notes) per minute
        'volume'  : 0.50,         # 50% without accent          
        'noteOnPercent' : 0.80,   # Normal on/off time of a note
        'ticksPerWhole' : 256*4,  # Plenty of resoultion with 256 ticks per beat (quarter note)
        # Length attributes can carry between notes
        'note_len' : 4,           # Music input default is quarter note
        'note_dots' : 0,          # Number of dots (none by default)
        'note_plet' : '',         # Triplets and duplets (none by default)
        # Octave numbers can carry between notes
        'note_octave' : 4,        # Middle C is C4
    }

    # Add the name of the track to the MIDI file (this is just informative)
    data = []
    for n in name:
        data.append(ord(n))
    ret.append(MetaEvent(0,3,data))

    wait_before = 0 # This is a note's "off time" after it has been on

    for line in track:                
        text = line['text']
        if text.startswith(':'):
            # Special music commands
            if text.lower().startswith(':voice'):
                prg = int(text[7:].strip())
                evt  = MIDIChannelProgramChangeEvent(0,note_defaults['channel'],prg)
                ret.append(evt)
            elif text.lower().startswith(':tempo'):
                i = text.find('=')
                note_defaults['tempo'] = int(text[i+1:].strip())
                dv = 60_000_000 // note_defaults['tempo']
                a = (dv>>16) & 0xFF
                b = (dv>>8) & 0xFF
                c = (dv) & 0xFF
                evt = MetaEvent(0,0x51,[a,b,c])
                ret.append(evt)
            else:
                raise Exception('Unknown "'+text+'"')
        else:
            notes = text.replace('|','').split()
            for note in notes:
                ni = parse_note(note,note_defaults)
                wait_before = process_note(ni,note_defaults,wait_before,ret)
            
    return ret

def _process(raw_lines):

    ret = MIDIFile()
    ret.format = 1
    ret.divis = 256

    # Start in Track 0 by default
    lines = [{'file':None,'line_number':0,'original_text':'Track 0','text':'Track 0'}]    

    for line in raw_lines:
        text = line['original_text']        
        i = text.find(';')
        if i>=0:
            text = text[:i]  
        text = text.strip()         
        line['text'] = text          
        if text:
            lines.append(line)               
    
    tracks = pull_tracks(lines)        
            
    ret.tracks = []    
    for name,track in tracks.items():
        track = process_track(name,track)
        track.append(MetaEvent(0,0x2F,[])) # End of Track
        ret.tracks.append(track)            
       
    return ret

def process_music_file(filename):
    raw_lines = []
    line_number = 0
    with open(filename) as f:
        for line in f:
            line_number+=1
            raw_lines.append({'file':filename,'line_number':line_number,'original_text':line.strip()})           
    return _process(raw_lines)

def process_music(text):
    raw_lines = []
    line_number = 0
    for line in text.split('\n'):
        line_number+=1
        raw_lines.append({'file':None,'line_number':line_number,'original_text':line})    
    return _process(raw_lines)

if __name__=="__main__":
        
    ret = process_music_file(sys.argv[1])

    print("NumTracks=%d Format=%d Division=%d" % (len(ret.tracks),ret.format,ret.divis))
    midi_diss.print_tracks(ret.tracks)        

    ret.write_file(sys.argv[2])
            
