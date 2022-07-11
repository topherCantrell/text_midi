'' Test the SnapAndProp's SD card and serial access
''
'' 1) Remove all jumpers from the SnapAndProp board
'' 2) Load this SnapAndProp.spin into the Propeller's EEPROM
'' 3) Load SnapAndProp.py into the RF100
''
'' 4) Use a micro SD card 2G or smaller (high density cards do not support the SPI
''    interface used here). Format the card in your PC (FAT or FAT32). Then create
''    a single text file in the root directory. Add a few lines of text, save, and
''    insert the card into the SnapAndProp socket.
''
'' 5) Use an LED or multimeter to see the voltage on J3 pin 12 (Propeller I/O P11).
''
'' 6) Leave the jumpers off and connect the PropPlug. Use the serial terminal on your
''    computer to interact with the Propeller as follows:
''
'' 7) Send 'A' to drive the pin high
'' 8) Send 'B' to drive the pin low
'' 9) Send 'D' to return data from the first file and increment the first byte in the file
'' 10) Experiment with 'A' and 'B' and 'D' and other characters. All characters will be
''     echoed back.
''
'' 11) Remove the PropPlug and insert jumpers JP3 and JP5. Use Portal to call "sendByte"
''     on the RF100 to interact with the Propeller.
'' 12) Repeat (7) through (10) using Portal

CON
        _clkmode        = xtal1 + pll16x
        _xinfreq        = 5_000_000

OBJ
  PST     : "Parallax Serial Terminal"
  SDCard  : "SDCard"

var
  byte buffer[512] ' Just one sector

PUB main | i, c

  ' Give the user time to switch from the Propeller Tool to the
  ' Serial Termial
  PauseMSec(2000)

  ' Mount the SD card (these are the port pins on the SnapAndProp board)
  '                          DO  CLK DI  CS
  i := SDCard.start(@buffer, 27, 26, 25, 24)

  '              Rx  Tx
  'PST.StartRxTx(0,  1,  0, 57600)  ' With jumpers JP2 and JP4
  PST.StartRxTx (31, 30, 0, 57600)  ' PropPlug (no jumpers) or jumpers JP3 and JP5
    
  dira[11] := 1 ' J3 pin 12
  outa[11] := 0
  
  repeat
    c := PST.CharIn
    PST.Char(c)
    case c
      "A" : outa[11] := 1
      "B" : outa[11] := 0
      "D" :
        ' Read the first sector from the first file
        SDCard.readFileSectors(@buffer,0,1)

        ' Modify the file
        buffer[0] := buffer[0] + 1
        SDCard.writeFileSectors(@buffer,0,1)

      ' Show 16 bytes of the file data
        i :=0
        repeat while i<16
          PST.hex(buffer[i],2)
          PST.char(32)
          ++i

PRI PauseMSec(Duration)
  waitcnt(((clkfreq / 1_000 * Duration - 3932) #> 381) + cnt)
