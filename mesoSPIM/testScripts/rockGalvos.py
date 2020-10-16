# -*- coding: utf-8 -*-
"""
Spyder Editor

Rock galvos back and forth to test output from NI DAQ interface

Galvo driver expects +- 10V

"""

import nidaqmx
import time
import numpy as np

with nidaqmx.Task() as task:
    task.ao_channels.add_ao_voltage_chan("pxiDev1/ao0")
    task.write([0, 1, 2, 3, 4, 5], auto_start = True)
    time.sleep(0.5)
    task.write(0, auto_start = True)
    
with nidaqmx.Task() as task:
    task.ao_channels.add_ao_voltage_chan("pxiDev2/ao0")
    task.write([10], auto_start = True)
    time.sleep(0.5)
    task.write(-10, auto_start = True)
    time.sleep(0.5)
    task.write(0, auto_start = True)
    
# make a sine wave
delay = 0.01
repeats = 4
nSamples = 50
scanRange = 3 # volts
goUntilInterrupt = True

x = np.linspace(0, 2*np.pi, nSamples)

galvo1 = nidaqmx.Task()
galvo1.ao_channels.add_ao_voltage_chan("pxiDev2/ao0")

galvo2 = nidaqmx.Task()
galvo2.ao_channels.add_ao_voltage_chan("pxiDev2/ao1")
rpts = 0
try:
    while rpts < repeats:
        for k in x:
            galvo1.write(scanRange*np.sin(k), auto_start = True)
            galvo2.write(scanRange*np.sin(k), auto_start = True)
            time.sleep(delay)
        if not goUntilInterrupt:
            rpts += 1
        
    galvo1.close()
    galvo2.close()
except KeyboardInterrupt:
    
    galvo1.write(0, auto_start = True)
    galvo2.write(0, auto_start = True)
    
    galvo1.close()
    galvo2.close()
        
        
