"""
Enable single laser lines through mesoSPIM interface.
Follow structure of mesoSPIM_LaserEnabler class

PRNicovich
AIBS

"""

import serial
import logging



class NicoLase_LaserEnabler:

	'''
	
	Class for interacting with digital laser modulation via NicoLase shield
	Control TTL inputs for up to 6 lasers
	
	Commands:
		Initialize
		Enable a line
		Disable all lines
		Enable all lines

	Future could add support for intensity along with on/off through octoDAC on same port
	'''
	
	def __init__(self, laserdict, port = 'COM3', timeout = 1, baud = 9600):
	'''
	Initialize laser enabler
	
	Input : laserdict - laserdict from .\config\demo_config.py
	
	'''
		self.laserenablestate = 'None'
		self.laserdict = laserdict
		
		# Startup communication
		logging.info('Connecting to NicoLase on port ' + port)
		self.serial = serial.Serial(port)
		devID = self.getIdentification()
		if devID == returnMessages['DeviceID']
			pass
		else:
			logging.info("Initialization error in NicoLase. Disconnecting")
			self.close()
		
		
		self.distable_all()
		
	def _check_if_laser_in_laserdict(self, laser):
		'''
		Check if laser string is in laserdict
		
		Input : laser - string; query laser name
		
		Returns : bool for if laser is key in laserdict
		'''
		
		if laser in self.laserdict:
			return True
		else:
			raise ValueError("Laser not in the configuration")


	def enable(self, laser):
	
		'''
		Turn on line defined by laserdict[laser]
		
		Input - laser; string
		
		'''
		
		if self._check_if_laser_in_laserdict(laser):
			self.serial.write(laserdict[laser] + '\n') # Set sequence as defined in laserdict
													   # Correct syntax here?
			self.serial.write(b'Q\n') # Open pseudo-shutter
			self.laserenablestate = laser
			
		else:
			pass
				
    def enable_all(self):
        '''Enables all laser lines.'''
        self.serial.write(b'F\n') # Set programmed pattern to B111111
		self.serial.write(b'Q\n') # Open pseudo-shutter
        self.laserenablestate = 'all on'

    def disable_all(self):
        '''Disables all laser lines.'''
        self.serial.write(b'O\n') # Close pseudo-shutter
        self.laserenablestate = 'off'
 

    def state(self):
        """ Returns laserline if a laser is on, otherwise "False" """
        return self.laserenablestate 