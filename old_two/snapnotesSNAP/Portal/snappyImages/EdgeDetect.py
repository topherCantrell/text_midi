from synapse.switchboard import * 

pinValue = False

@setHook(HOOK_STARTUP)
def _onBoot():    
    global pinValue
    setPinDir(0, False)
    setPinPullup(0, True)
    
    #monitorPin(0,True)
    #setRate(0,3)
    
    initUart(0, 57600)
    flowControl(0, False)
    mcastSerial(1,2)
    #ucastSerial('\x04\xC7\x42')
    crossConnect(DS_UART0, DS_TRANSPARENT)    

@setHook(HOOK_1MS)
def _oneMSTick():
    global pinValue
    v = readPin(0)
    if v!=pinValue:
        pinValue = v
        if pinValue == False:
            mcastRpc(1,1,'resetPropeller',True)
            #rpc('\x04\x00\x4A','resetPropeller')
        