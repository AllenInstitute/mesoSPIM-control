# -*- coding: utf-8 -*-
"""
Created on Thu Oct 15 14:25:22 2020

@author: rustyn

Confirm triggering of HamCam, leading to triggering of galvo waveform

master_trigger_out_line fires
  HamCam triggered
  camera_trigger_source triggered
    galvo_etl_task_line ramps


"""

import nidaqmx
import time
import numpy as np
from scipy import signal

# In HCImage, set to External (Light Sheet) triggering
# Output trigger enabled, with Trigger 1 set to Positive; Programmable; HSYNC
# Click 'Live' in Capture tab of HCImage before running this script
# , 'pxiDev1/ao0', 'pxiDev1/ao1'

acquisition_hardware = {'master_trigger_out_line' : '/pxiDev2/port0/line0',
                        'camera_trigger_source' : '/pxiDev2/PFI0',
                        'galvo_etl_task_line' : ['pxiDev2/ao0', 'pxiDev2/ao1', 'pxiDev1/ao0', 'pxiDev1/ao1'],
                        'galvo_etl_task_trigger_source' : '/pxiDev2/PFI0'}

galvoParameters = {'samplerate' : 100000,
                   'sweeptime' : 1.0,
                   'frequency' : 19.9,
                   'amplitude' : 2.5,
                   'offset' : 0,
                   'dutycycle' : 50,
                   'phase' : np.pi/2}

def sawtooth(
    samplerate = 100000,    # in samples/second
    sweeptime = 0.4,        # in seconds
    frequency = 10,         # in Hz
    amplitude = 0,          # in V
    offset = 0,             # in V
    dutycycle = 50,          # dutycycle in percent
    phase = np.pi/2,          # in rad
    ):
    '''
    Returns a numpy array with a sawtooth function

    Used for creating the galvo signal.

    Example:
    galvosignal =  sawtooth(100000, 0.4, 199, 3.67, 0, 50, np.pi)
    '''

    samples =  int(samplerate*sweeptime)
    dutycycle = dutycycle/100       # the signal.sawtooth width parameter has to be between 0 and 1
    t = np.linspace(0, sweeptime, samples)
    # Using the signal toolbox from scipy for the sawtooth:
    waveform = signal.sawtooth(2 * np.pi * frequency * t + phase, width=dutycycle)
    # Scale the waveform to a certain amplitude and apply an offset:
    waveform = amplitude * waveform + offset

    return waveform


# Set up output trigger
camTrigger = nidaqmx.Task()
camTrigger.do_channels.add_do_chan(acquisition_hardware['master_trigger_out_line'])
camTrigger.timing.ref_clk_src = "PXIe_Clk100" # Must explicitly state this to match what is used in analog 
                                              # Required with pxiDev2 used for both triggering and analog
                                              # See https://github.com/ni/nidaqmx-python/blob/master/nidaqmx_examples/ai_multi_task_pxie_ref_clk.py

# Set up waveforms
'''Create Galvo waveforms:'''
galvoWaveform = sawtooth(galvoParameters['samplerate'],
                                 galvoParameters['sweeptime'],
                                 galvoParameters['frequency'],
                                 galvoParameters['amplitude'],
                                 galvoParameters['offset'],
                                 galvoParameters['dutycycle'],
                                 galvoParameters['phase'])

'''Create ETL waveforms:'''
etlWaveform = sawtooth(galvoParameters['samplerate'],
                                 galvoParameters['sweeptime'],
                                 galvoParameters['frequency']/10,
                                 galvoParameters['amplitude'],
                                 2.5,
                                 galvoParameters['dutycycle'],
                                 galvoParameters['phase'])


waveform = np.stack((galvoWaveform, galvoWaveform, etlWaveform, etlWaveform))


# Set up galvo task + analog output trigger
galvoETLTask = nidaqmx.Task()

if isinstance(acquisition_hardware['galvo_etl_task_line'], list):
    galvoETLchannels = nidaqmx.utils.flatten_channel_string(acquisition_hardware['galvo_etl_task_line'])
elif isinstance(acquisition_hardware['galvo_etl_task_line'], str):
    galvoETLchannels = acquisition_hardware['galvo_etl_task_line']
else:
    raise('Incorrect type for galvo_etl_task_line key')
    
    
galvoETLTask.ao_channels.add_ao_voltage_chan(galvoETLchannels)

galvoETLTask.timing.cfg_samp_clk_timing(rate = galvoParameters['samplerate'],
                                            sample_mode = nidaqmx.constants.AcquisitionType.FINITE,
                                            samps_per_chan = int(galvoParameters['samplerate']*galvoParameters['sweeptime']))

galvoETLTask.triggers.start_trigger.cfg_dig_edge_start_trig(acquisition_hardware['galvo_etl_task_trigger_source'])


# Bundle waveform array for both galvos and both ETLs
galvoETLTask.write(waveform)
galvoETLTask.start()


# Trigger camera
camTrigger.write(True, auto_start=True)
time.sleep(0.001)
camTrigger.write(False, auto_start = True)

# '''Wait until everything is done - this is effectively a sleep function.'''
galvoETLTask.wait_until_done()

camTrigger.stop()
camTrigger.close()

galvoETLTask.stop()
galvoETLTask.close()





