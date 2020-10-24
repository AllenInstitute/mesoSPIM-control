#!/usr/bin/python
#
## @file
"""
RS232 interface to a Applied Scientific Instrumentation MS2000 stage.

Hazen 3/09
Adam Glaser 07/19
PRN 05/20

"""
try:
    import RS232 as RS232
except:
    from . import RS232 as RS232
    
import serial
from sys import exc_info as ErrorInfo

## MS2000
#
# Applied Scientific Instrumentation MS2000 RS232 interface class.
#
class MS2000(RS232.RS232):

    ## __init__
    #
    # Connect to the MS2000 stage at the specified port.
    #
    # @param port The RS-232 port name (e.g. "COM1").
    # @param wait_time (Optional) How long (in seconds) for a response from the stage.
    #
    def __init__(self, **kwds):

        self.live = True
        self.um_to_unit = 10.0
        self.unit_to_um = 0.1
        self.unit_to_deg = 0.001
        self.deg_to_unit = 1000.
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.m = 0.0
        self.n = 0.0
        self.t = 0.0

        if isinstance(kwds['port'], str):
            '''
            Port supplied as string
            Open new connection on that port
            '''
        
            self.closeOnDestroy = True
            try:
                # open port
                super().__init__(**kwds)
            except:
                self.live = False
                print("ASI Stage is not connected? Stage is not on?")
                
        elif isinstance(kwds['port'], serial.Serial):
            '''
            Port supplied as existing serial port connection
            Use this existing connection to communicate to stage
            Do not close on class instance destruction
            '''
            self.closeOnDestroy = False
            
            try:
                # Open port with supplied **kwds
                super().__init__(**kwds)
            except:
                self.live = False
                print('ASI stage did not initialize on supplied serial port')
            
        else:
            raise("Supply port as string or serial.Serial instance")

            
    def __del__(self):
        '''
        Class destructor method
        Close serial port if stage was opened by providing serial port string
        
        '''
        if self.closeOnDestroy:
            self.shutDown()

    def reset(self):
        resp = self.commWithResp("~", waitTime = 1)

    ## getMotorStatus
    #
    # @return True/False if the stage is moving.
    #
    def getMotorStatus(self):
        response = self.commWithResp("/")
        return response

    ## getStatus
    #
    # @return True/False if we are actually connected to the stage.
    #
    def getStatus(self):
        return self.live

    ## goAbsolute
    #
    # @param axis - X, Y, or Z.
    # @param pos position.
    #
    def goAbsolute(self, axis, pos, bwait):
        if self.live:
            
            if (axis == 'T'):
                p = self.scaleASIinput(pos, isRotation = True)
            else:
                p = self.scaleASIinput(pos)
            
            self.commWithResp("M " + axis + "=" + str(p))
            if bwait == True:
                response = self.getMotorStatus()
                while response[0] == 'B':
                    response = self.getMotorStatus()

    ## goRelative
    #
    # @param x Amount to move the stage in x in um.
    # @param y Amount to move the stage in y in um.
    #
    def goRelative(self, axis, pos, bwait):
        if self.live:
            if (axis == 'T'):
                p = self.scaleASIinput(pos, isRotation = True)
            else:
                p = self.scaleASIinput(pos)

            self.commWithResp("R " + axis + "=" + str(p))
            if bwait == True:
                response = self.getMotorStatus()
                while response[0] == 'B':
                    response = self.getMotorStatus()
    ## jog
    #
    # @param x_speed Speed to jog the stage in x in um/s.
    # @param y_speed Speed to jog the stage in y in um/s.
    #
    def jog(self, x_speed, y_speed):
        pass
#        if self.live:
#            vx = x_speed * 0.001
#            vy = y_speed * 0.001
#            self.commWithResp("S X=" + str(vx) + " Y=" + str(vy))

    ## joystickOnOff
    #
    # @param on True/False enable/disable the joystick.
    #
    def joystickOnOff(self, on):
        pass
        #if self.live:
        #    if on:
        #        self.commWithResp("!joy 2")
        #    else:
        #        self.commWithResp("!joy 0")

    ## getPosition
    #
    # @return [stage x (um), stage y (um), stage z (um)]
    #
    def getPosition(self, axis = '', verbose = False):
        if self.live:
           # try:
            if len(axis) == 0:
                
                queryResp = self.commWithResp("W X Y Z T M N")
                if verbose:
                    print(queryResp)
                    print(queryResp.split(" "))
                    
                [self.x, self.y, self.z, self.t, self.m, self.n] = self.commWithResp("W X Y Z T M N").split(" ")[1:7] # Watch order of return vs query here
                
                self.x = self.scaleASIoutput(self.x) # convert to um
                self.y = self.scaleASIoutput(self.y) # convert to um
                self.z = self.scaleASIoutput(self.z) # convert to um
                self.m = self.scaleASIoutput(self.m) # convert to um
                self.n = self.scaleASIoutput(self.n) # convert to um
                
                self.t = self.scaleASIoutput(self.t, isRotation = True) # convert to deg

                return [self.x, self.y, self.z, self.n, self.t]
					
            else:
                self.x = self.commWithResp(axis)
                return [self.x]
					
            #except:
             #   print("Stage Error in ms2000.getPosition")
              #  return [-1, -1, -1, -1, -1]
               # raise
            
        else:
            return [0.0, 0.0, 0.0, 0.0, 0.0]
    
    # Return value from raw getAxisPosition as int of position value only
    def stripIntPosition(self, postString):
        '''
        
        Parameters
        ----------
        postString : String
            Raw string from getAxisPosition. Expected to be in format ":A val1 val2 ... \r\n", 
            where val1, val2, ... are positions of axes from getAxisPosition query

        Returns
        -------
        If postString contains >1 value, return list of ints
        If postString contains = 1 value, return int

        '''
        
        postVals = [int(x) for x in postString.split(' ')[1:-1]]
        
        if len(postVals) > 1:
            return postVals
        elif len(postVals) == 1:
            return postVals[0]
        else:
            return -1
        
    def scaleASIoutput(self, val, verbose = False, isRotation = False):
        '''
        Parameters
        ----------
        val : numeric
            Default stage position values from ASI are given as tenths of microns when
            queried with 'W' command. 
            Here make float and scale to microns

        Returns
        -------
        outVal = val, scaled from tenths of microns to microns and made float
                    if isRotation = True, this is scaled from degrees to counts
        '''

        if isRotation:
            outVal = self.unit_to_deg*float(val)
        else:
            outVal = self.unit_to_um*float(val)
        
        if verbose:
            print(val)
            print(outVal)
            
        return outVal  
    
    def scaleASIinput(self, val, verbose = False, isRotation = False):
        
        if isRotation:
            outVal = int(self.deg_to_unit*val)
        else:
            outVal = int(self.um_to_unit*val)
        
        if verbose:
            print(val)
            print(outVal)
            
        return outVal  
        
    # Add in axis query command
    def getAxisPosition(self, axis, debugMode = False, verbose = False):
        # Debug mode for returning whole raw string.  
        # If false, use stripIntPosition to return int or list of ints
        
        if self.live:
            try:
                
                whereNow = self.commWithResp("W " + axis)
                
                if verbose:
                    print("Axis " + axis + " at " + whereNow)
                    
                if debugMode:
                    return whereNow
                else:
                    return self.scaleASIoutput(self.stripIntPosition(whereNow))
            except:
                print('Stage Error on axis position query')
                return -1
            
            
        else:
            return -1

    ## setBacklash
    #
    # @param backlash. 0 (off) or 1 (on)
    #
    def setBacklash(self, backlash):
        if self.live:
            self.commWithResp("B X=" + str(backlash))

    ## scan
    #
    # @param activate stage scan
    #
    def scan(self,bwait):
        if self.live:
            self.commWithResp("SCAN")
            if bwait == True:
                response = self.getMotorStatus()
                while response[0] == 'B':
                    response = self.getMotorStatus()

    ## setScanR
    #
    # @param x. START
    # @param y. STOP
    # @param z. ENC_DIVIDE

    ## setScanF
    #
    # @param scan_f. 0 (raster) or 1 (serpentine)
    #
    def setScanF(self, scan_f):
        if self.live:
            self.commWithResp("SCANF =" + str(scan_f))

    ## setScanR
    #
    # @param x. START
    # @param y. STOP
    # @param z. ENC_DIVIDE
    #
    def setScanR(self, x, y):
        if self.live:
            x = round(x,3)
            y = round(y,3)
            self.commWithResp("SCANR X=" + str(x) + " Y=" + str(y))

    ## setScanV
    #
    # @param x. START
    # @param y. STOP
    # @param z. NUMBER OF LINES
    # @param f. OVERSHOOT FACTOR
    #
    def setScanV(self, x):
        if self.live:
            x = round(x,3)
            self.commWithResp("SCANV X=" + str(x))

    ## setTTL
    #
    # @param scan_f. 0 (on) or 1 (off)
    #
    def setTTL(self, ttl):
        if self.live:
            self.commWithResp("TTL X=" + str(ttl))

    ## setVelocity
    #
    # @param axis - X, Y, or Z.
    # @param vel Maximum velocity.
    #
    def setVelocity(self, axis, vel):
        if self.live:
            vel = round(vel,5)
            self.commWithResp("S " + axis + "=" + str(vel))

    ## zero
    #
    # Set the current stage position as the stage zero.
    #
    def zero(self):
        if self.live:
            self.commWithResp("Z")
			
	
    def goHome(self):
        if self.live:
            self.commWithResp("!")
    
    def halt(self):
        if self.live:
            self.commWithResp('\\')

#
# The MIT License
#
# Copyright (c) 2014 Zhuang Lab, Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#