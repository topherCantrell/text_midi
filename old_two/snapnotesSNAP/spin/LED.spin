CON
  _clkmode        = xtal1 + pll16x
  _xinfreq        = 5_000_000

{{                                        
   Adafruit makes several I2C backpacks that drive arrays of LEDs.
   Your project controls the LEDs through I2C commands to the
   backpacks.

   http://www.adafruit.com/products/902 

   This project was written for the 8x8 bicolor LED matrix, but all of
   the backpacks use the HT16K33 chip. The software here can be tweaked
   for any particular backpack.

   The backpacks have built-on pullups for SDA and SCL. Thus hooking
   multiple backpacks to the same SCL/SDA lines will place these
   pullups in parallel and reduce the resistance. This will
   increase the current consumption.   
}}

var   
  byte ADDR        ' Backpack I2C address
  byte PIN_SCL     ' I/O pin connected to SCL
  byte PIN_SDA     ' I/O pin connected to SDA
  byte raster[16]  ' Raster buffer for (x,y) graphics

PUB TestMain
'' Just for testing the object (as a main)
'' Remove if you don't need to test
'
  Init($70,26)
  'writeDisplay(ADDR,0,16,@testPicture) ' Draw an alien
  clearRaster
  drawLine(0,0,7,7,2)
  drawLine(0,7,7,0,1) 
  drawRaster

DAT
'' Just for testing the object (as a main)
'' Remove if you don't need to test
'
testPicture

  byte  $18,$00,$3C,$00,$7E,$00,$DB,$24
  byte  $FF,$00,$24,$00,$5A,$5A,$A5,$A5 
  
      
PUB Init(i2cAddress,pinSCL)
'' Initialize the object with the given I2C-address and hardware pins.
'' The driver I am using requires SDA to be the next pin after SCL.
'
  ADDR := i2cAddress
  PIN_SCL := pinSCL
  PIN_SDA := pinSCL + 1 ' The I2C driver I used requires this connection    

  Initialize(PIN_SCL)
  
  setOscillator(ADDR,1)            ' Start the oscillator
  setBlink(ADDR,1,0)               ' Power on, no blinking                       
  setBrightness(ADDR,15)           ' Max brightness      
 
PUB setOscillator(address,on)
'' Turn the oscillator on (or off)
'
'  0010_xxx_p
'
  address := address << 1 ' # R/-W bit = 0 (write)
  on := on & 1
  on := on | $20
  
  Start(PIN_SCL)
  Write(PIN_SCL,address)
  Write(PIN_SCL,on)
  Stop(PIN_SCL)              

PUB setBlink(address,power,rate)
'' Set the display power and blink rate
''   rate = 00 = Off
''          01 = 2Hz
''          10 = 1Hz
''          11 = 0.5Hz
'
'  1000_x_rr_p
'
  address := address << 1 ' # R/-W bit = 0 (write)
  rate := rate & 3
  rate := rate << 1
  power := power & 1
  rate := rate | power
  rate := rate | $80
  
  Start(PIN_SCL)
  Write(PIN_SCL,address)
  Write(PIN_SCL,rate)
  Stop(PIN_SCL)
  

PUB setBrightness(address,level)
'' Set the display brightness
'' level: 0000=minimum, 1111=maximum
'
'  1110_vvvv
'
  address := address << 1 ' # R/-W bit = 0 (write)
  level := level & 15
  level := level | $E0
  
  Start(PIN_SCL)
  Write(PIN_SCL,address)
  Write(PIN_SCL,level)
  Stop(PIN_SCL)

PUB writeDisplay(address,register,count,data)
'' Write a number of data values beginning with the
'' given register.

  address := address << 1 ' # R/-W bit = 0 (write)
  Start(PIN_SCL)
  Write(PIN_SCL,address)
  Write(PIN_SCL,register)
    
  repeat while count>0
    Write(PIN_SCL,byte[data])
    data := data +1
    count := count -1
  
  Stop(PIN_SCL)

' Specific to the adafruit 8x8 bicolor backpack

PUB clearRaster | i
  repeat i from 0 to 15
    raster[i] := 0
    
PUB drawRaster
  writeDisplay(ADDR,0,16,@raster)

PUB setPixel(x,y,color) | p, ov1, ov2, mask
  p := y<<1
  mask := 1
  ov1 := color & 1
  ov2 := (color >> 1) & 1  
  ov1 := ov1 << x
  ov2 := ov2 << x
  mask := mask << x
  raster[p]   := raster[p]   & !mask | ov1
  raster[p+1] := raster[p+1] & !mask | ov2
  
pub drawLine(x0, y0, x1, y1, color) | dx, dy, difx, dify, sx, sy, ds
''Draw a straight line from (x0, y0) to (x1, y1)
'' By Phil Pilgrim:
'' http://forums.parallax.com/showthread.php/102051-Line-drawing-algorithm-anyone-create-one-in-spin?p=716238&viewfull=1#post716238
'
  difx := ||(x0 - x1)           'Number of pixels in X direciton.
  dify := ||(y0 - y1)           'Number of pixels in Y direction.
  ds := difx <# dify            'State variable change: smaller of difx and dify.
  sx := dify >> 1               'State variables: >>1 to split remainders between line ends.
  sy := difx >> 1
  dx := (x1 < x0) | 1           'X direction: -1 or 1
  dy := (y1 < y0) | 1           'Y direction: -1 or 1
  repeat (difx #> dify) + 1     'Number of pixels to draw is greater of difx and dify, plus one.
    setPixel(x0, y0,color)      'Draw the current point.
    if ((sx -= ds) =< 0)        'Subtract ds from x state. =< 0 ?
      sx += dify                '  Yes: Increment state by dify.
      x0 += dx                  '       Move X one pixel in X direciton.
    if ((sy -= ds) =< 0)        'Subtract ds from y state. =< 0 ?
      sy += difx                '  Yes: Increment state by difx.
      y0 += dy                  '       Move Y one pixel in Y direction.
 
  

                                      

' These are from Michael Green's basic I2C driver (see OBEX).
' Replace these with an object that has faster functions.
' These are pasted here to keep the demonstration self-contained.

PUB Initialize(SCL) | SDA              ' An I2C device may be left in an
   SDA := SCL + 1                      '  invalid state and may need to be
   outa[SCL] := 1                       '   reinitialized.  Drive SCL high.
   dira[SCL] := 1
   dira[SDA] := 0                       ' Set SDA as input
   repeat 9
      outa[SCL] := 0                    ' Put out up to 9 clock pulses
      outa[SCL] := 1
      if ina[SDA]                      ' Repeat if SDA not driven high
         quit                          '  by the EEPROM

PUB Start(SCL) | SDA                   ' SDA goes HIGH to LOW with SCL HIGH
   SDA := SCL + 1
   outa[SCL]~~                         ' Initially drive SCL HIGH
   dira[SCL]~~
   outa[SDA]~~                         ' Initially drive SDA HIGH
   dira[SDA]~~
   outa[SDA]~                          ' Now drive SDA LOW
   outa[SCL]~                          ' Leave SCL LOW
  
PUB Stop(SCL) | SDA                    ' SDA goes LOW to HIGH with SCL High
   SDA := SCL + 1
   outa[SCL]~~                         ' Drive SCL HIGH
   outa[SDA]~~                         '  then SDA HIGH
   dira[SCL]~                          ' Now let them float
   dira[SDA]~                          ' If pullups present, they'll stay HIGH

PUB Write(SCL, data) : ackbit | SDA
'' Write i2c data.  Data byte is output MSB first, SDA data line is valid
'' only while the SCL line is HIGH.  Data is always 8 bits (+ ACK/NAK).
'' SDA is assumed LOW and SCL and SDA are both left in the LOW state.
   SDA := SCL + 1
   ackbit := 0 
   data <<= 24
   repeat 8                            ' Output data to SDA
      outa[SDA] := (data <-= 1) & 1
      outa[SCL]~~                      ' Toggle SCL from LOW to HIGH to LOW
      outa[SCL]~
   dira[SDA]~                          ' Set SDA to input for ACK/NAK
   outa[SCL]~~
   ackbit := ina[SDA]                  ' Sample SDA when SCL is HIGH
   outa[SCL]~
   outa[SDA]~                          ' Leave SDA driven LOW
   dira[SDA]~~

PUB Read(SCL, ackbit): data | SDA
'' Read in i2c data, Data byte is output MSB first, SDA data line is
'' valid only while the SCL line is HIGH.  SCL and SDA left in LOW state.
   SDA := SCL + 1
   data := 0
   dira[SDA]~                          ' Make SDA an input
   repeat 8                            ' Receive data from SDA
      outa[SCL]~~                      ' Sample SDA when SCL is HIGH
      data := (data << 1) | ina[SDA]
      outa[SCL]~
   outa[SDA] := ackbit                 ' Output ACK/NAK to SDA
   dira[SDA]~~
   outa[SCL]~~                         ' Toggle SCL from LOW to HIGH to LOW
   outa[SCL]~
   outa[SDA]~                          ' Leave SDA driven LOW