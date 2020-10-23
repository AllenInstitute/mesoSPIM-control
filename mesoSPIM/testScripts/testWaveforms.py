# -*- coding: utf-8 -*-
"""
Created on Thu Oct 22 13:22:11 2020

@author: rustyn

Test script for waveform output for live image in mesoSPIM_Core.py

"""

import octoDAC_LaserWaveformGenerator as oD
import serial

ser = serial.Serial(port = 'COM3', baudrate = 115200)

oD.octoDAC_LaserWaveformGenerator(ser)

t = oD.echoWaveform()
print(t)




ser.close()