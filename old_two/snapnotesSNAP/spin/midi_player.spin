''************************
''*   MIDI file player   *
''************************
'' Author:   Andy Schenk, Insonix
'' Date:     March 2009

'' uses the PhaseMod GM Synthesizer to play the MIDI files of a play list.
'' Needs an SD card connected, and the MIDI files stored on the card.
'' Because the files are played directly from the card, only the MidiFile Format 0
'' is supported (all Tracks mixed down to one).


CON
  _clkmode        = xtal1 + pll16x
  _xinfreq        = 5_000_000

  SD_basepin      = 0       '<-- SD card
  Left            = 10      '<-- Audio Out pins
  Right           = 11
        
VAR    
  long  time, tq, ts, us
  byte  filename[16]

OBJ
  sd    : "fsrw"
  synth : "pm_synth_20"
  disp  : "TV_Text"         'or "VGA_Text" or "PC_Text"


DAT
playlist
                byte    "2001.mid",0
                byte    "NUTRAC.MID",0
                byte    "BOHEMIAN.MID",0
                byte    "POPCORN0.MID",0
                byte    "WHITERSH.MID",0
listend

      
PUB Main
  disp.start(12)                                        '<-- Display basepin
  synth.start(Left,Right,2)                             'start synth with 20 voices
  ifnot sd.mount(SD_basepin)                            'init SD card
    filename := @playlist                               'start Play List
    repeat
      disp.out(0)
      disp.str(string("Playing: "))
      disp.str(filename)
      waitcnt(clkfreq*2+cnt)
      midiplay(filename)                                'play the file
      filename += strsize(filename)+1
    until filename => @listend                          'next file
    synth.allOff
    disp.str(string(13,"done"))
  else
    disp.str(string("SD card not found"))

  repeat
    

PUB midiplay(name)  | lg, dt, b, v, st, d1, d2, ch
  us := clkfreq / 1_000_000                             'ticks / microsecond
  b := st := d1 := d2 := v := 0
  ifnot sd.popen(name,"r")
    sd.pread(@v,4)
    if v == "M" + "T"<<8 + "h"<<16 + "d"<<24            'Header ID
      sd.pread(@v,4)                                    'Header Len
      v~
      sd.pread(@v,2)                                    'Format
      if v <> 0
        disp.str(string("only Format 0 supported"))
      else
        sd.pread(@v,2)                                  'Tracks
        sd.pread(@v,2)                                  'Ticks/Quarter
        tq := v>>8 + (v&255)<<8
        ts := 500_000 / tq                              'default Tempo 120 BPM
        sd.pread(@v,4)                                  '"MTrk"
        sd.pread(@v,4)                                  'Track length
        lg := v>>24 + (v>>16&255)<<8 + (v>>8&255)<<16
        time := cnt
        repeat
          sd.pread(@b,1)                                'get delta time
          lg--
          dt := b & $7F
          repeat while b>127
            sd.pread(@b,1)
            lg--
            dt := dt<<7 + (b & $7F)
          time := time + dt*us*ts
          repeat until time-cnt < 0                     'wait deltatime
          b~
          sd.pread(@b,1)                                'MIDI byte
          if b > 127
            st := b                                     'new status byte
          elseif st==$FF
            st~
          ch := st & $0F
          d1~
          d2~
          case st & $F0                                 'decode MIDI Event
            $90: sd.pread(@d1,1)                        'Note 
                 sd.pread(@d2,1)                        'Velocity
                 lg -= 3
                 if d2>0
                   synth.noteOn(d1,ch,d2)               'Note On
                   show(15,ch+1,string(127),-1)
                 else
                   synth.noteOff(d1,ch)                 'Note Off if Vel=0
                   show(15,ch+1,string("."),-1)
            $80: sd.pread(@d1,1)                        'Note Off 
                 sd.pread(@d2,1)                        'Velocity
                 lg -= 3
                 synth.noteOff(d1,ch)
                 show(15,ch+1,string("."),-1)
                 if ch==9
                   show(20,ch+1,string(">"),d1)
            $A0: sd.pread(@d1,1)                        'Poly AfterTouch 
                 sd.pread(@d2,1)                        '(not supported)
                 lg -= 3
            $C0: sd.pread(@d1,1)                        'Prg Change 
                 lg -= 2
                 synth.prgChange(d1,ch)
                 show(0,ch+1,string("Ch:"),ch+1)
                 show(6,ch+1,string("Prg:"),d1)
            $D0: sd.pread(@d1,1)                        'Mono AfterTouch 
                 lg -= 2                                '(not supported)
            $B0: sd.pread(@d1,1)                        'Controller (nr) 
                 sd.pread(@d2,1)                        'value
                 lg -= 3
                 if d1==7
                   synth.volContr(d2,ch)                '7=Vol
                 if d1==10
                   synth.panContr(d2,ch)                '10=Pan
            $E0: sd.pread(@d1,1)                        'Pitch Bender 
                 sd.pread(@d2,1)                        '(not supported!)
                 lg -= 3
            $F0: sd.pread(@d1,1)                        'Meta Event
                 v~
                 if st==$F0 or st==$F7                  'SysEx
                   repeat
                     sd.pread(@v,1)
                     lg--
                     d1--
                   until v==$F7 or b=< 0
                   d1~
                 else
                   lg -= 2
                   sd.pread(@b,1)                       'Len
                   repeat while b>0                     'read meta data
                     sd.pread(@d2,1)
                     v := v<<8 + d2
                     b--
                     lg--
                   if d1==81                            'Tempo
                     ts := v / tq
            0:   sd.pread(@d1,1)                        'Meta Event Running status
                 lg -= 2
                 sd.pread(@b,1)                         'Len
                 repeat while b>0                       'read meta data
                   sd.pread(@d2,1)
                   v := v<<8 + d2
                   b--
                   lg--
            
        until lg < 1
    else
      disp.str(string("No MIDI file"))
    sd.pclose
'    synth.allOff
  else
    disp.str(string("File not found"))

PUB show(x,y,strp,val)                                  ''visualize MIDI events
  if y<12
    disp.out(10)
    disp.out(x)
    disp.out(11)
    disp.out(y)
    disp.str(strp)
    if val=>0
      disp.dec(val)
    disp.out(" ")
     
{{
 ---------------------------------------------------------------------------
                Terms of use: MIT License                                   
 ---------------------------------------------------------------------------
   Permission is hereby granted, free of charge, to any person obtaining a  
  copy of this software and associated documentation files (the "Software"),
  to deal in the Software without restriction, including without limitation 
  the rights to use, copy, modify, merge, publish, distribute, sublicense,  
    and/or sell copies of the Software, and to permit persons to whom the   
    Software is furnished to do so, subject to the following conditions:    
                                                                            
   The above copyright notice and this permission notice shall be included  
           in all copies or substantial portions of the Software.           
                                                                            
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,  
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER   
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING   
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER     
                       DEALINGS IN THE SOFTWARE.                            
 ---------------------------------------------------------------------------
}}  