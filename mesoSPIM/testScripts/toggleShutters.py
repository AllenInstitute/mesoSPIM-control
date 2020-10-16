# -*- coding: utf-8 -*-
"""
Created on Thu Oct 15 11:42:50 2020

@author: rustyn

Test connection to shutters TTL lines on NI DAQ ports

Should have connections:
    Shutter left - pxiDev1/port0/line0
    Shutter right - pxiDev1/port0/line1
    
Shutters must be on and in External mode.  If so, power LED will be green on 
power-up and ENABLE LED dark.  When ENABLE button pressed, the ENABLE LED will
blink green.  Deviation from this behavior can be rectified by consulting 
manual for controller (see page 11 for Default to On, page 9 for ENABLE modes)

When this script is executed, there should be four audible clicks 
(shutter 1 on/off, shutter 2 on/off)
    

"""

import nidaqmx
import time

shutter1 = nidaqmx.Task()
shutter1.do_channels.add_do_chan("pxiDev1/port0/line0")

shutter2 = nidaqmx.Task()
shutter2.do_channels.add_do_chan("pxiDev1/port0/line1")

shutter1.write(True)
time.sleep(0.5)
shutter1.write(False)
shutter1.close()

time.sleep(0.5)

shutter2.write(True)
time.sleep(0.5)
shutter2.write(False)
shutter2.close()