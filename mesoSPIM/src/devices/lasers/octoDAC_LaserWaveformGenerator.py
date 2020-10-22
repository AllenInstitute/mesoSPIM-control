# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 14:51:24 2020

@author: Rusty Nicovich
"""

import numpy as np
import time
import serial

class octoDAC_LaserWaveformGenerator:
    
    def __init__(self, serialObject, waitTime = 10, endOfLineChar = '\n', verbose = False):
        
        self.end_of_line = endOfLineChar # newline character
        self.wait_time = waitTime
        self.verbose = verbose
        
        if isinstance(serialObject, serial.Serial):
            
            # Use existing serial object
            self.ser = serialObject
        elif isinstance(serialObject, str):
            # Open new serial port object
            self.ser = serial.Serial(port = serialObject, baudrate = 115200)
            
    def sendCommand(self, command):
        self.ser.flush()
        outString = command + self.end_of_line
        self.ser.write(outString.encode())
            
            
    def writeAndRead(self, command):
        """
        Send a command and wait (a little) for a response.
        """
        self.sendCommand(command)
        time.sleep(10 * self.wait_time)
        response = ""
        response_len = self.ser.inWaiting()
        while response_len:
            response += self.ser.read(response_len)
            time.sleep(self.ser.wait_time)
            response_len = self.ser.inWaiting()
        if len(response) > 0:
            return response
            

    
    def setChannel(self, chan, setVal):
        """ 
        Set channel to value
        """      
        if (chan > 0) and (chan < 9):
            
            sendVal = self.numToShortInteger(setVal)
            sendString = str(chan) + ' ' + sendVal
            
            self.writeAndRead(sendString)
            
        else:
            print('Incorrect channel name. Channel must be 0-8')
        
	# Upload waveform
	# Helper function for 'a' command
    def uploadWaveform(self, waveArray):
        """
		Upload waveform in waveArray to device
		Input : waveArray - numpy array, M x 3.  
							[{channel, timepoint, amplitude],...]
		
		"""
		
        if len(waveArray.shape) == 1:
			# Array is single row
            uploadString = 'a {};{};{}'.format(str(int(waveArray[0])), 
											   str(int(waveArray[1])), 
											   str(int(waveArray[2])))
		
            self.sendCommand(uploadString)
			
        else:
		
			# Waveform will be distorted if not in order of second column
            waveArray = waveArray[np.argsort(waveArray[:, 1])]
		
			# Waveform max length is 128 points total. 
			# Truncate here and log warning on truncation.
			
            if (waveArray.shape[1] >= 128):
                waveArray = waveArray[:128,:]
			
			
			# Upload each line in waveArray
			
            for wv in waveArray:
                uploadString = 'a {};{};{}'.format(str(int(wv[0])), 
											   str(int(wv[1])), 
											   str(int(wv[2])))
		
            self.sendCommand(uploadString)            
        
        
    # c
    def clearWaveform(self):
        """
        Clear waveform registers
        """
        ret = self.writeAndRead('c')
				
	
	# e
    def echoWaveform(self):
        """ 
		Echo current waveform on device
		"""
        ret = self.writeAndRead('e')
        return ret
		
	# f
    def freeRunWaveform(self):
        """ 
		Free-run waveform until stop command is given.
		"""
        ret = self.writeAndRead('f')
		
	# k 
    def stopWaveform(self):
        """
		Stop a free-running waveform after next loop.
		"""
        ret = self.writeAndRead('k')
		
	# n 
    def singleShotWaveform(self):
        """
		Execute single shot of waveform
		"""
        ret = self.writeAndRead('n')
		
	# t 
    def waveformOnTrigger(self):
        """
		Set device to execute single shot of waveform on 
		trigger to pin 2 (MASTERFIRE w/ NicoLase shield)
		"""
        ret = self.writeAndRead('t')
	 
    # s 0
    def closeShutter(self):
        """ 
        Set all outputs to LOW
        Close pseudo-shutter
        """
        ret = self.writeAndRead('s 0')
        
    # s 1    
    def openShutter(self):
        """ 
        Set all outputs to stored value
        Open pseudo-shutter
        """
        ret = self.writeAndRead('s 1')
        
    # ? s
    def queryShutter(self):
        """ 
        Set all outputs to stored value
        Open pseudo-shutter
        """
        ret = self.writeAndRead('? s')
        return ret  
    
    # ? w
    def queryWaveformInProcess(self):
        """
        Query if waveform is active.
        """
        idn = self.writeAndRead('? w')
        return idn
    
    # x
    def clearRegister(self):
        """ 
        Clear DAC register.
        Set all outputs to 0
        """
        idn = self.writeAndRead('x')
        
    # y
    def getIdentification(self):
        """ identification query """
        idn = self.writeAndRead('y')
        return idn 
    
    # Wrappers using NI syntax   
    def write(self, waveArray):
        if self.verbose:
            print('Uploading waveform')
            print(waveArray)
        self.uploadWaveform(waveArray)
        
    def start(self):
        if self.verbose:
            print('Start waveform on trigger')
        self.waveformOnTrigger()
    
    def wait_until_done(self, timeout = 10):
        '''
        Python-side pause to let waveform complete before proceeding
        timeout is max time to wait (in seconds)
        '''
        callTime = time.time()
        
        returnNow = False
        while not(returnNow):
            
            waveformGoing = self.queryWaveformInProcess()
            timeElapsed = time.time() - callTime
            
            if (waveformGoing == '0') or (timeElapsed > timeout):
                returnNow = True
                
    def stop(self):
        if self.verbose:
            print('Stop waveform')
        self.stopWaveform()
        
    def close(self):
        if self.verbose:
            print('Close waveform')
        self.clearRegister()
        
    