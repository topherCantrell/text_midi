import Loader

class OTAPropLoader(Loader.Loader):
    
    def __init__(self, port):
        self.serInit(57600,port)   
        
    # TODO: override the serial methods to handle over-the-air             
 
def showProgress(msg):
    print msg

if __name__ == "__main__":
    Loader.upload("COM6","d:/workspaceee/snapnotesSNAP/spin/SerialMIDI.eeprom", 
                  eeprom=True, run=True, progress=showProgress )