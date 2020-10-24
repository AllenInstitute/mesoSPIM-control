# -*- coding: utf-8 -*-
"""
Created on Thu Oct 22 13:22:11 2020

@author: rustyn

Test script for waveform output for live image in mesoSPIM_Core.py

"""

import octoDAC_LaserWaveformGenerator as oD
import serial
import time
import numpy as np

ser = serial.Serial(port = 'COM3', baudrate = 115200, timeout = 1)
octoDAC = oD.octoDAC_LaserWaveformGenerator(ser, verbose = True)
r = octoDAC.getIdentification()
print(r)

# # Upload waveform 
waveform = np.array([[1, 0, 65535],
                      [2, 0, 65535], 
                      [3, 0, 65535], 
                      [4, 0, 65535], 
                      [5, 0, 65535], 
                      [6, 0, 65535],
                      [1, 100000, 0], 
                      [2, 100000, 0], 
                      [3, 100000, 0], 
                      [4, 100000, 0], 
                      [5, 100000, 0], 
                      [6, 100000, 0], 
                      [1, 200000, 0],
                      [2, 200000, 0],
                      [3, 200000, 0],
                      [4, 200000, 0],
                      [5, 200000, 0],
                      [6, 200000, 0]])

octoDAC.uploadWaveform(waveform)
# print(octoDAC.echoWaveform())

# octoDAC.invokeTestPattern() # Confirmed works to get all lasers to flash

'''
# Trigger free run of waveform

octoDAC.freeRunWaveform()

time.sleep(10)

octoDAC.stop()

'''

# Triggered waveform 
# Feed PRIMARY TRIGGER on NicoLase a reasonable pulse train (~3 Hz)
octoDAC.start()



# ser.close()
# del(octoDAC)