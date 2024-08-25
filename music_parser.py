import string
import sys
import logging

from midi_events import MetaEvent, SystemExclusiveEvent
from midi_events import MIDIChannelNoteEvent
from midi_events import MIDIChannelProgramChangeEvent
from midi_events import MIDIChannelControlChangeEvent
from midi_events import MIDIChannelPolyphonicKeyPressureEvent
from midi_events import MIDIChannelRunningStatusEvent

#import midi_track_merge
import midi_diss
from midi_file import MIDIFile

LOGGER = logging.getLogger(__name__)

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
    print('>>>',tracks.keys())
    return tracks

def parse_note(text,info,err_text=None):
   
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
    note_right = text[i:]

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

    # If no length was given, use the last note's value
    if note_len:
        note_len = int(note_len)        
    else:
        note_len = info['note_len']
        note_dots = info['note_dots']
        note_plet = info['note_plet']
   
    # Now for the pitch(es)

    note_pitches = [] # Each is a tuple: (note_name,accidental)    
    for pitch in [note_right] + par_notes:        
        if not pitch[0] in 'CDEFGABR':
            raise Exception('Invalid note name "'+pitch+'" in "'+err_text+'"')
        note_name = pitch[0]
        note_right = pitch[1:]    

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
            note_octave = info['note_octave']
        else:
            if note_name=='R':            
                raise Exception('Rests do not have octaves "'+pitch+'" in "'+err_text+'"')
            note_octave = int(note_octave)
        while note_right and note_right[0] in '+-':
            if note_name=='R':            
                raise Exception('Rests do not have octaves "'+pitch+'" in "'+err_text+'"')
            octave_offset = note_right[0]
            note_right = note_right[1:]
            if octave_offset=='+':
                note_octave += 1
            else:
                note_octave -= 1
        if note_right:            
            raise Exception('Invalid syntax right of note name "'+pitch+'" in "'+err_text+'"')
        note_pitches.append((note_name,note_accidental,note_octave))
        info['note_octave'] = note_octave

        if note_name=='R':            
            if note_accidental:
                raise Exception('Rests do not have accientals "'+pitch+'" in "'+err_text+'"')
   
    if len(note_pitches)>1:
        for pitch in note_pitches:
            if pitch[0]=='R':
                raise Exception('Rests not allowed in parallel notes "'+err_text+'"')          

    # Update the defaults for the next note to access
    #info['note_octave'] = note_octave # Done in the pitch loop
    info['note_len'] = note_len        
    info['note_dots'] = note_dots
    info['note_plet'] = note_plet
    info['note_accent'] = note_accent
    info['note_tie'] = note_tie
    info['note_pitches'] = note_pitches    

NOTE_VALUES = { # offsets within an octave            
               'C':0,
               'D':2,
               'E':4,
               'F':5,
               'G':7,
               'A':9,
               'B':11,              
               }

def get_midi_note_number(note_name,note_accidental,note_octave):
    """Combine octave, note-name, and accidentals to get the midi note number

    Midi octaves go from -1 through 9. Midi note 0 is C-1. Midi note 12 is C0.
    Midi note 120 is C9. Our input system doesn't support negative numbers, but
    you can specify octave "-1" with "0-".
    """
    note_octave += 1    
    ret = note_octave * 12 + NOTE_VALUES[note_name]
    if note_accidental == '#':
        ret += 1
    elif note_accidental == 'b':
        ret -= 1
    return ret

def process_note(info,previous_note,wait_before,events):
    # It is all about volume (velocity) and duration. The volume is given on
    # the NoteOn event. The duration is the distance between NoteOn and NoteOff.  

    # First, the duration (on and off)

    LOGGER.debug(f'wait_before:{wait_before} info: {info}')

    bl = info['note_len']
    if info['note_plet'] == 't':
        bl = int(bl * 3 / 2)
    elif info['note_plet'] == 'd':
        bl = int(bl * 2 / 3)
    note_len = info['ticksPerWhole'] / bl

    # TODO handle multiple dots
    if info['note_dots']:
        note_len = note_len + note_len/2

    # Second, the volume

    # TODO apply accents
    # TODO caller needs to keep up with increase/decrease volume over time
    velocity = int(info['volume']*127)

    # If this is a rest, we just accumulate the total time    
   
    # TODO apply staccato, etc
    if info['note_pitches'][0][0]=='R':
        return int(note_len) + wait_before          

    # Number of ticks the note is on and off
    len_on = int(note_len * info['noteOnPercent'])
    len_off = int(note_len - len_on)

    # If the last note was tied into this one, then there was already a noteOn. No
    # need for that now. Otherwise generate noteOn events for this note.
   
    if previous_note and previous_note['note_tie']:
        # print('Last note was tied into this ... no noteOns')
        pass
    else:
        # All notes on
        for note_name,note_accidental,note_octave in info['note_pitches']:
            note = get_midi_note_number(note_name,note_accidental,note_octave)
            events.append(MIDIChannelNoteEvent(wait_before,info['channel'],True,note,velocity))
            wait_before = 0 # Reset time-till-next-event

    # If this note is tied into the next, then we accumulate the time just like
    # we did a rest (but after we turned notes on if needed)

    if info['note_tie']:
        # print('This note is tied into next ... just accumulate')
        return int(note_len) + wait_before

    # Looks like this note is not tied to the next. We need to generate noteOff events here.

    # print('This note is not tied into next ... turn off the events')
    # All notes off    
    for note_name,note_accidental,note_octave in info['note_pitches']:
        note = get_midi_note_number(note_name,note_accidental,note_octave)
        events.append(MIDIChannelNoteEvent(wait_before+len_on,info['channel'],False,note,0))        
        len_on = 0
        wait_before = 0
        first = False

    return len_off

def process_track(name,track):    
    ret = [] # List of midi events

    note_info = {  
        'channel' : 0,            # Can be changed per-track
        'tempo'   : 120,          # By default, midi is 120 beats (quarter notes) per minute
        'volume'  : 0.80,         # 80% without accent          
        'noteOnPercent' : 0.80,   # Normal on/off time of a note
        'ticksPerWhole' : 256*4,  # Plenty of resoultion with 256 ticks per beat (quarter note)
        # Length attributes can carry between notes
        'note_len' : 4,           # Music input default is quarter note
        'note_dots' : 0,          # Number of dots (none by default)
        'note_plet' : '',         # Triplets and duplets (none by default)        
        # Octave can carry between notes
        'note_octave' : 4,
        # These are specified by every note        
        'note_tie' : False,
        'note_pitches': None, # (note_name, note_accidental, note_octave)
    }

    # Add the name of the track to the MIDI file (this is just informative)
    data = []
    for n in name:
        data.append(ord(n))
    ret.append(MetaEvent(0,3,data))

    wait_before = 0 # This is a note's "off time" after it has been on
    previous_note = None # TODO ultimately we want to make a list of parsed notes so the process_note can have them all at once
    for line in track:                
        text = line['text']
        if text.startswith(':'):
            if text.lower().startswith(':channel'):
                ch = int(text[9:].strip())
                note_info['channel'] = ch
            # Special music commands
            elif text.lower().startswith(':voice'):
                prg = int(text[7:].strip())
                evt  = MIDIChannelProgramChangeEvent(0,note_info['channel'],prg)
                ret.append(evt)
            elif text.lower().startswith(':tempo'):
                i = text.find('=')
                note_info['tempo'] = int(text[i+1:].strip())
                dv = 60_000_000 // note_info['tempo']
                a = (dv>>16) & 0xFF
                b = (dv>>8) & 0xFF
                c = (dv) & 0xFF
                evt = MetaEvent(0,0x51,[a,b,c])
                ret.append(evt)
            elif text.lower().startswith(':volume'):
                vol = int(text[8:].strip())
                evt  = MIDIChannelControlChangeEvent(0,note_info['channel'],7,vol)
                ret.append(evt)
            else:
                raise Exception('Unknown "'+text+'"')
        else:
            notes = text.replace('|','').split()
            for note in notes:
                parse_note(note,note_info)
                wait_before = process_note(note_info,previous_note,wait_before,ret)
                previous_note = dict(note_info) # Make a copy of the last note
           
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

    # py -m music_parser input.txt output.mid -printMidi

    logging.basicConfig(level='INFO')
       
    ret = process_music_file(sys.argv[1])

    print("NumTracks=%d Format=%d Division=%d" % (len(ret.tracks),ret.format,ret.divis))
    if len(sys.argv)>3 and sys.argv[3]=='-printMidi':
        midi_diss.print_tracks(ret.tracks)        

    ret.write_file(sys.argv[2])