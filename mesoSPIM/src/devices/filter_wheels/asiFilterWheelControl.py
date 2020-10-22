# -*- coding: utf-8 -*-
"""
Created on Thu Oct 15 16:56:57 2020

@author: rustyn

Class to drive ASI filter wheel
Build on top of Serial
"""

import serial 
import time


class ASIFilterWheel(object):
    
    def __init__(self, COMport, filterdict, baudrate=115200):
        '''
        Initialization method
        
        COMport : port to connect.  String (eg 'COM3') or established serial.Serial object
        filterdict : dict of filter names, positions
        baudrate (optional) : baud rate of connection to com port
        
        Want so that if COMport is supplied as string, make a new connection to that port
        If supplied as serial.Serial object, then use existing connection
        
        '''        
    
        if isinstance(COMport, serial.Serial):
            # Serial port exists. Use that to drive filter wheel
            
            self.ser = COMport
            self.COMport = COMport.port
            self.baundrate = COMport.baudrate   
            self.closeOnDestructor = False
            
        elif isinstance(COMport, str):
            # COMport given as string
            
            self.ser = serial.Serial(port = COMport, baudrate = baudrate)
            self.COMport = COMport
            self.baudrate = baudrate
            self.closeOnDestructor = True
            
        else:
            raise('COMport variable must be string or serial.Serial object')        
        
        # Common properties
        self.filterdict = filterdict
        self.double_wheel = False
        

        ''' Delay in s for the wait until done function '''
        self.wait_until_done_delay = 0.5

        """
        If the first entry of the filterdict has a tuple
        as value, it is assumed that it is a double-filterwheel
        to change the serial commands accordingly.

        TODO: This doesn't check that the tuple has length 2.
        """
        self.first_item_in_filterdict = list(self.filterdict.keys())[0]

        if type(self.filterdict[self.first_item_in_filterdict]) is tuple:
            '''Double filter wheels unsupported
            '''
            self.double_wheel = False
            
    def spin_wheel(self, timeToSpin = 5):
        '''
        Parameters
        ----------
        timeToSpin : numeral, optional
            Number of seconds to spin filter wheel. The default is 5.

        Returns
        -------
        None.

        '''
        
        self.ser.write('SF 1\r'.encode())
        time.sleep(timeToSpin)
        self.ser.write('SF 0\r'.encode()) 
        
    def _check_if_filter_in_filterdict(self, filter):
        '''
        Checks if the filter designation (string) given as argument
        exists in the filterdict
        '''
        if filter in self.filterdict:
            return True
        else:
            raise ValueError('Filter designation not in the configuration')

    def set_filter(self, filter, wait_until_done=False):
        '''
        Moves filter using the pyserial command set.

        No checks are done whether the movement is completed or
        finished in time.


        '''
        if self._check_if_filter_in_filterdict(filter) is True:
            filterNumber = self.filterdict[filter]
            sendString = 'MP ' + str(filterNumber) + '\r'
            
            self.ser.write(sendString.encode())
            self.ser.flush()
            
            
            if wait_until_done:
                ''' Wait a certain number of seconds. This is a hack
                '''
    
                
                time.sleep(self.wait_until_done_delay)
    
            else:
                pass
                '''
                Double filter wheel unsupported here for ASI filter wheels
            '''

        else:
            print(f'Filter {filter} not found in configuration.')
            
    def reset(self):
        self.ser.write('~ \r'.encode())
        time.sleep(1)
            
    def __del__(self):
        '''
        Class destructor method
        If class initialized by making a new connection to a COM port, 
        close port when instance is destroyed
        '''
        
        if self.closeOnDestructor:
            self.ser.close()

        
