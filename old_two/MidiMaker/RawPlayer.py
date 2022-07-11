import serial
import time

ser = serial.Serial('COM6', 57600, timeout=1) 

def convertTextEvent(evt):
    words = evt.split(":")
    if words[0]=='NoteOn':
        return str(0x90 | int(words[1]))
    elif words[0]=='ProgramChange':
        return str(0xC0 | int(words[1]))
    elif words[0]=='ControllerChange':
        return str(0xB0 | int(words[1]))
    else:
        raise Exception("Unknown event '"+words[0]+"'")   

with open('test.txt') as f:
    content = f.readlines()
    
pos = 0
while pos<len(content):
    s = content[pos]
    pos = pos + 1
    if ";" in s:
        s = s[0:s.index(";")]
    if not s.startswith("#"):
        continue
    words = s[1:].split()
    delta = int(words[0])
    if words[1] == "MetaEvent": 
        continue
    if ":" in words[1]:
        words[1] = convertTextEvent(words[1])
      
    print delta, words[1:]
      
    time.sleep(delta/580.0)
    r = ''
    for w in words[1:]:
        r = r + chr(int(w))
    ser.write(r)
    
    
