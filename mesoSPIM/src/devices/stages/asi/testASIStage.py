# -*- coding: utf-8 -*-
"""
Created on Wed Oct 14 16:29:04 2020

@author: rustyn

Test axes of stage through ms2000.py interface

WARNING - This moves stages!  
If stage limits are not set, this could crash stage into other components


mesoSPIM w/ ASI stages has axes:
    X - Sample left-right, as viewed on camera
    Y - Sample up-down, as viewed on camera
    Z - Sample in-out, as viewed on camera
    M - Zoom body and camera move left-right
    N - Zoom body and camera move in-out
    T - Sample rotate

"""

import ms2000
import serial

# 'Silicon Labs CP210x USB to UART Bridge' in Device Manager
# indicates COM port to use. Check baud rate in Termite.

comPort = 'COM10'
baudrate = 115200

stagesInstalled = ['X', 'Y', 'Z', 'M', 'N', 'T']

# Connect to stage
print('Opening stage on ' + comPort + ' with new COM port')
asiStage = ms2000.MS2000(port = comPort, baudrate = baudrate)

# Print current position of each axis expected
for k in stagesInstalled:
    whereNow = asiStage.getAxisPosition(k)
    print(whereNow)
    
print(asiStage.getPosition())

print("Closing stage on " + comPort)
del(asiStage)

'''
Test by supplying existing serial port to ms2000
'''
print("Opening stage using existing serial.Serial connection")
asiSer = serial.Serial(port = comPort, baudrate = baudrate)

asiStage = ms2000.MS2000(port = asiSer)

# Print current position of each axis expected
for k in stagesInstalled:
    whereNow = asiStage.getAxisPosition(k)
    print(k + ' = ' + str(whereNow))
    
asiStage.goRelative("T", 90, True)
print('T = ' + str(asiStage.getAxisPosition('T')))

#asiStage.reset()
    
print("Closing stage on " + comPort)
del(asiStage)

asiSer.close()