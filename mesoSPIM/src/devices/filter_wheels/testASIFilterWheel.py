# -*- coding: utf-8 -*-
"""
Created on Thu Oct 15 16:50:27 2020

@author: rustyn

Move ASI filter wheel around

"""

import asiFilterWheelControl
import time


filterdict = {'Empty-Alignment' : 0, # Every config should contain this
              '440-40' : 1,
              '510-42' : 2,
              '562-40' : 3,
              '585-40' : 4,
              '640-40' : 5,
              '679-41' : 6}

'''
ASI filter wheel made by supplying string to available com port

Filter wheel should spin for 5 seconds, then go to 5 discrete positions

'''

asiWheel = asiFilterWheelControl.ASIFilterWheel('COM10', filterdict)

asiWheel.spin_wheel()

asiWheel.set_filter('562-40')
time.sleep(0.5)
asiWheel.set_filter('440-40')
time.sleep(0.5)
asiWheel.set_filter('562-40')
time.sleep(0.5)
asiWheel.set_filter('640-40')
time.sleep(0.5)
asiWheel.set_filter('510-42')
time.sleep(0.5)

del(asiWheel)

time.sleep(2)

'''

ASI filter wheel made by supplying open COM port object

Filter wheel should go to 5 discrete positions

'''

import serial

ser = serial.Serial(port = 'COM10', baudrate = 115200)

asiWheel = asiFilterWheelControl.ASIFilterWheel(ser, filterdict)

asiWheel.set_filter('562-40')
time.sleep(0.5)
asiWheel.set_filter('440-40')
time.sleep(0.5)
asiWheel.set_filter('562-40')
time.sleep(0.5)
asiWheel.set_filter('640-40')
time.sleep(0.5)
asiWheel.set_filter('510-42')
time.sleep(0.5)

ser.close()


