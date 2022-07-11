import time
import serial

ser = serial.Serial(baudrate=115200, timeout=0)
ser.port = 'COM6'
ser.open()

ser.setDTR(1)
time.sleep(1.0)
ser.setDTR(0)
time.sleep(1.0)

ser.close()