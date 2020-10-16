# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.


pxiDev1
pxiDev2

Driver software must be open and set to 'Analog' mode
ETL driver expects 0-5v

"""

import nidaqmx
import time
import numpy as np

    
# make a sine wave
delay = 0.05
repeats = 4
nSamples = 100
scanRange = 5 # volts
goUntilInterrupt = True

x = np.linspace(0, 2*np.pi, nSamples)

etl1 = nidaqmx.Task()
etl1.ao_channels.add_ao_voltage_chan("pxiDev1/ao0")

etl2 = nidaqmx.Task()
etl2.ao_channels.add_ao_voltage_chan("pxiDev1/ao1")
rpts = 0
try:
    while rpts < repeats:
        for k in x:
            etl1.write(0.5*scanRange*np.sin(k)+2.5, auto_start = True)
            etl2.write(0.5*scanRange*np.sin(k)+2.5, auto_start = True)
            time.sleep(delay)
        if not goUntilInterrupt:
            rpts += 1
        
    etl1.close()
    etl2.close()
except KeyboardInterrupt:
    
    etl1.write(0, auto_start = True)
    etl2.write(0, auto_start = True)
    
    etl1.close()
    etl2.close()
        
        
