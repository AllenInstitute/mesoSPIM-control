# -*- coding: utf-8 -*-
"""
Created on Thu Oct 15 14:25:22 2020

@author: rustyn

Confirm triggering of HamCam, counting of Hsync pulses


"""

import nidaqmx
import time

# In HCImage, set to External (Light Sheet) triggering
# Output trigger enabled, with Trigger 1 set to Positive; Programmable; HSYNC
# Click 'Live' in Capture tab of HCImage before running this script

acquisition_hardware = {'master_trigger_out_line' : 'pxiDev2/port0/line0',
                        'camera_trigger_source' : 'pxiDev2/PFI0',
                        'camera_trigger_out_line' : 'pxiDev2/ctr0'}
fs = 100e6
nb_channels = 128

# Set up trigger
camTrigger = nidaqmx.Task()
camTrigger.do_channels.add_do_chan(acquisition_hardware['master_trigger_out_line'])





# Set up counter
hSyncCounter = nidaqmx.Task()
hSyncCounter.ci_channels.add_ci_count_edges_chan(acquisition_hardware['camera_trigger_out_line'], 'ctr0')
hSyncCounter.channels.ci_count_edges_count_reset_term = acquisition_hardware['camera_trigger_source']

# CTR 0 src=> PFI 2
hSyncCounter.timing.cfg_samp_clk_timing(rate=fs, source="ctr0", sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS, samps_per_chan=nb_channels+1)

hSyncCounter.channels.ci_count_edges_count_reset_active_edge = nidaqmx.constants.Edge.RISING
# Specify whether to reset the count on the active edge specified with ci_count_edges_count_reset_term.
hSyncCounter.channels.ci_count_edges_count_reset_enable = True
hSyncCounter.start()

  self.camera_trigger_task.co_channels.add_co_pulse_chan_time(ah['camera_trigger_out_line'],
                                                                    high_time=self.camera_high_time,
                                                                    initial_delay=self.camera_delay)

        self.camera_trigger_task.triggers.start_trigger.cfg_dig_edge_start_trig(ah['camera_trigger_source'])




# Trigger camera
camTrigger.write(True)
time.sleep(0.001)
camTrigger.write(False)

# Count number of edges detected
print(hSyncCounter.read(number_of_samples_per_channel=nidaqmx.constants.READ_ALL_AVAILABLE))


hSyncCounter.stop()
hSyncCounter.close()
camTrigger.close()




