# -*- coding: utf-8 -*-
"""
Created on Thu Oct 22 13:22:11 2020

@author: rustyn

Test script for waveform output for live image in mesoSPIM_Core.py

"""

import octoDAC_LaserWaveformGenerator as oD
import serial
import time

ser = serial.Serial(port = 'COM3', baudrate = 115200, timeout = 1)
print('1')
print('2')
octoDAC = oD.octoDAC_LaserWaveformGenerator(ser)
print('3')
r = octoDAC.getIdentification()
print(r)
print('3.5')
t = octoDAC.getIdentification()
print('4')
print(t)

print('5')
ser.close()
print('6')
del(octoDAC)