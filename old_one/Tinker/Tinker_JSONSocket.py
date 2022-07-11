import socket
import json

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("localhost",1234))

data = {
        'command': 'doGoodStuff',
        'data': [1,2,3,4]
        }

s.send(json.dumps(data)+"\n")

