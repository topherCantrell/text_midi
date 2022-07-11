CON
  _clkmode        = xtal1 + pll16x
  _xinfreq        = 5_000_000

  ' Audio Out pins  
  Left            = 10  ' 4 for demo board 
  Right           = -1  ' -1 For mono

OBJ
    synth   : "pm_synth_20"
    PST     : "Parallax Serial Terminal"
    eeprom  : "Propeller EEprom"

var                                 
  word channelMask
        
PUB Main | com,chan,chanBits, key,vel,v,nd
    
  ' For debuggig: Give the user time to switch from the Propeller Tool to theSerial Termial
  ' PauseMSec(2000)

  ' This player can listen to several midi channels at once. The list of active
  ' channels is kept in the last two bytes of EEPROM to survive power cycles.
  '
  ' Every player listens to a MIDI system-exclusive command to set the list of
  ' midi-channels. Either power up one unit at a time or send the serial command
  ' to just the target unit.

  ' Read the list of active MIDI channels from EEPROM
  eeprom.ToRam(@channelMask, @channelMask+1, $7FFE)
  if channelMask==0      ' Zero (uprogrammed) means ...
    channelMask := $FFFF ' ... ALL channels 
    
  ' Start listening for serial MIDI
  PST.StartRxTx (31, 30, 0, 57600)
  synth.start(Left,Right,2)
  
  ' Audible that we are running  
  signOnTone
  'foreverChord
     
  PauseMSec(10)
  
  synth.allOff
  
  ' Remember: we have to eat the serial bytes even if they are not for us

  com := $10 ' Impossible from the stream. This is the "search for first command" case.
   
  repeat    
    v := PST.CharIn         ' Next byte from the stream
    if v>$7F                ' This is a new command                            
      com := v >> 4         '   Mark the new command (upper nibble)
      chan := v & $0F       '   Lower nibble is channel
      chanBits := 1<< chan  '   Make bit mask 
      nd := PST.CharIn      '   Get the first data byte
    else                    ' This is a continuation of the last command
      nd := v               '   This is the first data byte of the continuation
            
    case com    
      $8 : ' $8x KK VV -> NoteOff: KEY VELOCITY
        ' key is in nd
        vel := PST.CharIn
        if (chanBits&channelMask)<>0 
          synth.noteOff(nd,chan)
          
      $9 : ' $9x KK VV -> NoteOn: KEY VELOCITY
        ' key is in nd
        vel := PST.CharIn            
        if (chanBits&channelMask)<>0              
          if vel==0 ' MIDI allows vel=0 to mean note off
            synth.noteOff(nd,chan)
          else
            synth.noteOn(nd,chan,vel)
                       
      $A : ' $Ax KK TT -> AfterTouch: KEY TOUCH
        ' key is in nd
        vel := PST.CharIn
        
      $B : ' $Bx CC VV -> Controller: NUM VALUE (only handling the "volume" controller)
        ' num is in nd
        vel := PST.CharIn
        if nd== 7 ' $Bx 07 VV -> Volume: VALUE (0-127)
          if (chanBits&channelMask)<>0  
            synth.volContr(vel,chan) ' Controller takes 0..255, incoming 0..127
            
      $C : ' $Cx PP -> Patch: PATCH
        ' patch is in nd
        if (chanBits&channelMask)<>0  
          synth.prgChange(nd,chan)
          
      $D : ' $Dx PP -> Pressure: PRES
        ' pres is in nd (nothing more to read)
        
      $E : ' $Ex BB BB -> PitchBlend: BLEND BLENDs
        ' blend is in nd
        vel := PST.CharIn

      ' These are "System Exclusive Events". We should NOT get Meta Events (FF)
      $F : ' $F0 7D 00 ... F7 Set channel-parameters where "..." is the list of channels to include one byte each (0 - 15)
        ' id is in nd
        if nd==$7D   ' 7D is "development" ... us
          nd := PST.CharIn ' Command: 0 for channel, 1 for firmware
          if nd<>0
            downloadFirmware ' Reboots the unit. Does not return.
          channelMask := 0
          repeat
            nd := PST.CharIn ' next byte from the stream
            if nd==$F7       ' read to ...
              quit           ' ... F7
           channelMask := channelMask | (1<<(nd&$0F)) ' Should only be 16 bits
          if channelMask==0        ' All 0's mean ...
            channelMask := $FFFF   ' ... everything
          eeprom.FromRam(@channelMask, @channelMask+1, $7FFE) ' Store the new params in EEPROM
      
        else
         ' Consume (ignore) any other Fx command
         repeat while (nd<>$F7)
           key := PST.CharIn
           
      $10 :
      ' This is the beginning case when we are waiting for a command byte

PUB signOnTone
  synth.noteOn(69,0,64) ' MIDI note 69 (A440) on channel 0 velocity 127 

PUB foreverChord
  ' Audible that we are running  
  synth.noteOn(69,0,64) ' MIDI note 69 (A440) on channel 0 velocity 127
  synth.noteOn(71,0,64) ' MIDI note 69 (A440) on channel 0 velocity 127
  synth.noteOn(73,0,64) ' MIDI note 69 (A440) on channel 0 velocity 127
  repeat


PUB downloadFirmware | ch, p, t
  ' F0 7D 01  cm cl ...
  '   cccc is the checksum

  synth.allOff ' Stop sounds during download
  
  ch := (PST.CharIn<<8) | PST.CharIn    ' Checksum

  p := $4000               ' Starting here
  t := 0                   ' Start checksum
  repeat while p<>$8000    ' The entire download
    byte[p] := PST.CharIn  '   Next byte
    t := t + byte[p]       '   Checksum it
    t := t & $FFFF         '   Two byte checksum
    p := p + 1             '   Bump pointer
    
  if ch<>t                 ' Bad checksum. Do nothing.
    synth.noteOn(40,0,80)
    PauseMSec(1000)
    reboot

  ' Write the block to serial ram
  eeprom.FromRam($4000, $7FFF, $0000)

  synth.noteOn(80,0,80)
  PauseMSec(1000)
  reboot
                                                                                                           
PRI PauseMSec(Duration)
  waitcnt(((clkfreq / 1_000 * Duration - 3932) #> 381) + cnt)