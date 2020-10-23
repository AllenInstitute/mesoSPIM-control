# -*- coding: utf-8 -*-
"""
Created on Thu Oct 22 14:23:43 2020

@author: rustyn
"""

# -*- coding: utf-8 -*-
"""
Created on Fri Mar 13 16:41:37 2020
@author: Rusty Nicovich
Helper class to communicate with octoDAC.
Inputs : serialDevice - pySerial port, already open (115200 baud)
         verbose (optional) - print all returned bytes if true
"""

import time
import numpy as np
import serial


returnMessages = {
    'CMD_NOT_DEFINED': 0x15,
    'DeviceID' : 'octoDAC'}

ENCODING = 'utf-8'

def octoDACStart(comPort, baud, timeOut = 1):
    
    """
    Helper function to start a serial object like octoDAC or NicoLase
    
    Inputs : comPort - string; com port to use for this object
             baud - int; baud rate for serial port.  NicoLase is set to 115200
             timeOut - int; timeout time for port in seconds.  Default is 1    
             
    Returns : serial port ready to pass to octoDACDriver object
    """

    ser1 = serial.Serial(comPort, baud, timeout = timeOut)
    time.sleep(3)
    ser1.flushInput()
    ser1.reset_input_buffer()
        
    return ser1

class octoDACDriver():
    """
    Class for communicating with octoDAC Arduino Shield + sketch
    
    """
    def __init__(self, serialDevice, verbose = False):

        # Once connected, check that port actually has octoDAC on the receiving end
        self.serial = serialDevice
        print(self.serial.name)
        self.verbose = verbose
        print(self.getIdentification())
        print(self.getIdentification())
        print(self.getIdentification())
        devID = self.getIdentification()
        if devID == returnMessages['DeviceID']:
            if self.verbose:
                print('Connected to octoDAC on port ' + self.serial.port)
                
            # Set all ports to 0
            for k in range(1,8):
                self.setChannel(k, 0)
        else:
            print("Initialization error! Disconnecting!\n")
            self.serial.close()
            
    def __del__(self):
        self.serial.close()
            
    def numToShortInteger(self, setVal):
        """
        Utility function to convert input value to (two byte?) integer
        """
        if (setVal >= 0) and (setVal < 65536):
            shortVal = str(setVal)
        elif (setVal > 65535):
            shortVal = str(65535)
        else:
            shortVal = str(0)
            
        return shortVal
    
    def writeAndRead(self, sendString):
        """
        Helper function for sending to serial port, returning line
        """
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()
        sendString += '\n'
        retCode = self.serial.write(sendString.encode(ENCODING))
        ret = self.serial.readline().decode(ENCODING).strip()
        
        if self.verbose:
            print(ret)
            
        return
    
# Upload waveform
# Helper function for 'a' command
    def uploadWaveform(self, waveArray):

#        Upload waveform in waveArray to device
#        Input : waveArray - numpy array, M x 3.  
#                            [{channel, timepoint, amplitude],...]
#   
#       channel = 1-8
#       timepoint = waypoint timepoint (microseconds)
#       amplitude = 0-65535

        
        if len(waveArray.shape) == 1:
            # Array is single row
            uploadString = 'a {};{};{}'.format(str(int(waveArray[0])), 
                                               str(int(waveArray[1])), 
                                               str(int(waveArray[2])))
        
  
            self.writeAndRead(uploadString)
            
        else:
        
            # Waveform will be distorted if not in order of second column
            waveArray = waveArray[np.argsort(waveArray[:, 1])]
        
            # Waveform max length is 128 points total. 
            # Truncate here and log warning on truncation.
            
            if (waveArray.shape[1] >= 100):
                waveArray = waveArray[:100,:]
                print("Waveform array longer than 100 lines. Truncating to first 100 lines.")
            
            
            # Upload each line in waveArray
            
            for wv in waveArray:
                uploadString = 'a {};{};{}'.format(str(int(wv[0])), 
                                               str(int(wv[1])), 
                                               str(int(wv[2])))
                
#                print(uploadString)
                
                self.writeAndRead(uploadString)
                time.sleep(.1)

    # 0-8 XX
    def setChannel(self, chan, setVal):
        """ 
        Set channel to value
        """      
        if (chan > 0) and (chan < 9):
            
            sendVal = self.numToShortInteger(setVal)
            sendString = str(chan) + ' ' + sendVal
            
            self.writeAndRead(sendString)
            
        else:
            print('Input chan : ' + str(chan))
            print('Incorrect channel name. Channel must be 0-8')
            
    # c
    def clearWaveform(self):
        """
        Clear current waveform from device
        """
        self.writeAndRead('c')

    # e
    def echoWaveform(self):
        """ 
        Echo current waveform on device
        """
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()
        retCode = self.serial.write('e\n'.encode(ENCODING))
        rd = self.serial.read(1000).decode(ENCODING)
        print(rd)
        
        
        #self.writeAndRead('e')
        
        
    # f
    def freeRunWaveform(self):
        """ 
        Free-run waveform until stop command is given.
        """
        self.writeAndRead('f')
        
    # k 
    def stopWaveform(self):
        """
        Stop a free-running waveform after next loop.
        """
        self.writeAndRead('k')
        
    # n 
    def singleShotWaveform(self):
        """
        Execute single shot of waveform
        """
        self.writeAndRead('n')
        
    # t 
    def waveformOnTrigger(self):
        """
        Set device to execute single shot of waveform on 
        trigger to pin 2 (MASTERFIRE w/ NicoLase shield)
        """
        self.writeAndRead('t')
     
    # s 0
    def closeShutter(self):
        """ 
        Set all outputs to LOW
        Close pseudo-shutter
        """
        self.writeAndRead('s 0')
        
    # s 1    
    def openShutter(self):
        """ 
        Set all outputs to stored value
        Open pseudo-shutter
        """
        self.writeAndRead('s 1')
        
    # ? s
    def queryShutter(self):
        """ 
        Set all outputs to stored value
        Open pseudo-shutter
        """
        retCode = self.serial.write('? s\n'.encode(ENCODING))
        idn = self.serial.readline().decode(ENCODING).strip()
        return idn 
        
    # y
    def getIdentification(self):
        """ identification query """
        retCode = self.serial.write('y\n'.encode(ENCODING))
        idn = self.serial.readline().decode(ENCODING).strip()
        return idn
    
    def close(self):
        self.serial.close()
        
    
    
    
    
if __name__ == '__main__':
    print("Testing octoDAC shield...")

    
    serPort = serial.Serial(port = 'COM3', baudrate = 115200, timeout = 1)
    time.sleep(1)
    oD = octoDACDriver(serPort, verbose = False)
    
    # Make ramp on CHAN2
    for k in range(0, 65536, 100):
        oD.setChannel(4, k) 
    
    # Blink CHAN2 3 times      
    for k in range(0, 3):
        oD.closeShutter()
        time.sleep(0.5)
        oD.openShutter()
        time.sleep(0.5)
        
    oD.closeShutter()
    
    del(oD)