# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 14:51:24 2020

@author: Rusty Nicovich
"""

import np
import logging

class octoDAC_LaserWaveformGenerator:
    
    def __init__(self, serialObject):
        # Use existing serial object
        self.ser = serialObject
        
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
		
			ret = self[uploadString]
			self.logReturn(ret)
			
		else:
		
			# Waveform will be distorted if not in order of second column
			waveArray = waveArray[np.argsort(waveArray[:, 1])]
		
			# Waveform max length is 128 points total. 
			# Truncate here and log warning on truncation.
			
			if (waveArray.shape[1] >= 128):
				waveArray = waveArray[:128,:]
				logging.info("Waveform array longer than 128 lines. Truncating to first 128 lines.")
			
			
			# Upload each line in waveArray
			
			for wv in waveArray:
				uploadString = 'a {};{};{}'.format(str(int(wv[0])), 
											   str(int(wv[1])), 
											   str(int(wv[2])))
		
				ret = self[uploadString]
				self.logReturn(ret)
                
    # c
    def clearWaveform(self):
        """
        Clear waveform registers
        """
        ret = self['c']
        self.logReturn(ret)
				
	
	# e
	def echoWaveform(self):
		""" 
		Echo current waveform on device
		"""
		ret = self['e']
		self.logReturn(ret)
		return ret
		
	# f
	def freeRunWaveform(self):
		""" 
		Free-run waveform until stop command is given.
		"""
		ret = self['f']
		self.logReturn(ret)
		
	# k 
	def stopWaveform(self):
		"""
		Stop a free-running waveform after next loop.
		"""
		ret = self['k']
		self.logReturn(ret)
		
	# n 
	def singleShotWaveform(self):
		"""
		Execute single shot of waveform
		"""
		ret = self['n']
		self.logReturn(ret)
		
	# t 
	def waveformOnTrigger(self):
		"""
		Set device to execute single shot of waveform on 
		trigger to pin 2 (MASTERFIRE w/ NicoLase shield)
		"""
		ret = self['t']
		self.logReturn(ret)
	 
    # s 0
    def closeShutter(self):
        """ 
        Set all outputs to LOW
        Close pseudo-shutter
        """
        ret = self['s 0']
        self.logReturn(ret)
        
    # s 1    
    def openShutter(self):
        """ 
        Set all outputs to stored value
        Open pseudo-shutter
        """
        ret = self['s 1']
        self.logReturn(ret)
        
    # ? s
    def queryShutter(self):
        """ 
        Set all outputs to stored value
        Open pseudo-shutter
        """
        idn = self['? s']
        self.logReturn(idn)
        return idn  
    
    # ? w
    def queryWaveformInProcess(self):
        """
        Query if waveform is active.
        """
        idn = self['? w']
        self.logReturn(idn)
        return idn
    
    # x
    def clearRegister(self):
        """ 
        Clear DAC register.
        Set all outputs to 0
        """
        ret = self['x']
        self.logReturn(ret)
        
    # y
    def getIdentification(self):
        """ identification query """
        idn = self['y']
        return idn 