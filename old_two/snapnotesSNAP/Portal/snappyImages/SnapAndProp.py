from synapse.switchboard import * 

#CONTROL_ADDR="\x00\x00\x01"

channelMask = 65535
description = 'SNAPNotes'

@setHook(HOOK_STARTUP)
def _onBoot():
    global channelMask, description
    initUart(0, 57600)
    flowControl(0, False)
    writePin(5,True) # Release the propeller's reset
    mcastSerial(1,2)
    #ucastSerial('\x05\xD5\xA4')
    crossConnect(DS_UART0, DS_TRANSPARENT)    
    
    description = loadNvParam(128)
    channelMask = loadNvParam(129)
    if description == None:
        description = 'SNAPNotes'
    if channelMask == None:
        channelMask = 65535
        
    reportInfo() # Tell the controller we powered up
    
def resetPropeller():
    # Pulse pin 5 (reset) low for 1MS
    pulsePin(5,1,False)
    
def setInfo(c,d):
    global channelMask, description
    channelMask = c
    description = d
    saveNvParam(128,description)
    saveNvParam(129,channelMask)
    
def reportInfo():
    global channelMask, description
    mcastRpc(1,2, "speakerInfo", channelMask, description)
    #rpc(CONTROL_ADDR, "speakerInfo", channelMask, description)
        
