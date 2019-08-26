'''
mesoSPIM Camera class, intended to run in its own thread
'''
import os
import time
import numpy as np

import tifffile

import logging
logger = logging.getLogger(__name__)

from PyQt5 import QtCore, QtWidgets, QtGui
'''
try:
    from .devices.cameras.hamamatsu import hamamatsu_camera as cam
except:
    logger.info('Error: Hamamatsu camera could not be imported')
'''
from .mesoSPIM_State import mesoSPIM_StateSingleton
from .utils.acquisitions import AcquisitionList, Acquisition

class mesoSPIM_Camera(QtCore.QObject):
    '''Top-level class for all cameras'''
    sig_camera_frame = QtCore.pyqtSignal(np.ndarray)
    sig_finished = QtCore.pyqtSignal()
    sig_update_gui_from_state = QtCore.pyqtSignal(bool)

    def __init__(self, parent = None):
        super().__init__()

        self.parent = parent
        self.cfg = parent.cfg

        self.state = mesoSPIM_StateSingleton()

        self.stopflag = False

        self.x_pixels = self.cfg.camera_parameters['x_pixels']
        self.y_pixels = self.cfg.camera_parameters['y_pixels']
        self.x_pixel_size_in_microns = self.cfg.camera_parameters['x_pixel_size_in_microns']
        self.y_pixel_size_in_microns = self.cfg.camera_parameters['y_pixel_size_in_microns']

        self.camera_line_interval = self.cfg.startup['camera_line_interval']
        self.camera_exposure_time = self.cfg.startup['camera_exposure_time']

        self.camera_display_live_subsampling = self.cfg.startup['camera_display_live_subsampling']
        self.camera_display_snap_subsampling = self.cfg.startup['camera_display_snap_subsampling']
        self.camera_display_acquisition_subsampling = self.cfg.startup['camera_display_acquisition_subsampling']

        ''' Wiring signals '''
        self.parent.sig_state_request.connect(self.state_request_handler)

        self.parent.sig_prepare_image_series.connect(self.prepare_image_series, type=3)
        self.parent.sig_add_images_to_image_series.connect(self.add_images_to_series)
        self.parent.sig_add_images_to_image_series_and_wait_until_done.connect(self.add_images_to_series, type=3)
        self.parent.sig_end_image_series.connect(self.end_image_series, type=3)

        self.parent.sig_prepare_live.connect(self.prepare_live, type = 3)
        self.parent.sig_get_live_image.connect(self.get_live_image)
        self.parent.sig_get_snap_image.connect(self.snap_image)
        self.parent.sig_end_live.connect(self.end_live, type=3)

        ''' Set up the camera '''
        if self.cfg.camera == 'HamamatsuOrcaFlash':
            self.camera = mesoSPIM_HamamatsuCamera2(self)
        elif self.cfg.camera == 'PhotometricsIris15':
            self.camera = mesoSPIM_PhotometricsCamera(self)
        elif self.cfg.camera == 'DemoCamera':
            self.camera = mesoSPIM_DemoCamera(self)

        self.camera.open_camera()

    def __del__(self):
        try:
            self.camera.close_camera()
        except Exception as error:
            logger.info('Error while closing the camera:', str(error))

    @QtCore.pyqtSlot(dict)
    def state_request_handler(self, dict):
        for key, value in zip(dict.keys(),dict.values()):
            # print('Camera Thread: State request: Key: ', key, ' Value: ', value)
            '''
            The request handling is done with exec() to write fewer lines of
            code.
            '''
            if key in ('camera_exposure_time',
                        'camera_line_interval',
                        'state',
                        'camera_display_live_subsampling',
                        'camera_display_snap_subsampling',
                        'camera_display_acquisition_subsampling'):
                exec('self.set_'+key+'(value)')
            # Log Thread ID during Live: just debugging code
            elif key == 'state':
                if value == 'live':
                    logger.info('Thread ID during live: '+str(int(QtCore.QThread.currentThreadId())))

    def set_state(self, value):
        pass

    @QtCore.pyqtSlot()
    def stop(self):
        ''' Stops acquisition '''
        self.stopflag = True

    def set_camera_exposure_time(self, time):
        '''
        Sets the exposure time in seconds

        Args:
            time (float): exposure time to set
        '''
        self.camera.set_exposure_time(time)
        self.camera_exposure_time = time
        self.sig_update_gui_from_state.emit(True)
        self.state['camera_exposure_time'] = time
        self.sig_update_gui_from_state.emit(False)

    def set_camera_line_interval(self, time):
        '''
        Sets the line interval in seconds

        Args:
            time (float): interval time to set
        '''
        self.camera.set_line_interval(time)
        self.camera_line_interval = time
        self.sig_update_gui_from_state.emit(True)
        self.state['camera_line_interval'] = time
        self.sig_update_gui_from_state.emit(False)

    def set_camera_display_live_subsampling(self, factor):
        self.camera_display_live_subsampling = factor

    def set_camera_display_snap_subsampling(self, factor):
        self.camera_display_snap_subsampling = factor

    def set_camera_display_acquisition_subsampling(self, factor):
        self.camera_display_acquisition_subsampling = factor

    @QtCore.pyqtSlot(Acquisition)
    def prepare_image_series(self, acq):
        '''
        Row is a row in a AcquisitionList
        '''
        logger.info('Camera: Preparing Image Series')
        #print('Cam: Preparing Image Series')
        self.stopflag = False

        ''' TODO: Needs cam delay, sweeptime, QTimer, line delay, exp_time '''

        self.path = acq['folder']+'/'+acq['filename']

        logger.info(f'Camera: Save path: {self.path}')
        self.z_start = acq['z_start']
        self.z_end = acq['z_end']
        self.z_stepsize = acq['z_step']
        self.max_frame = acq.get_image_count()

        self.fsize = self.x_pixels*self.y_pixels

        self.xy_stack = np.memmap(self.path, mode = "write", dtype = np.uint16, shape = self.fsize * self.max_frame)

        self.camera.initialize_image_series()
        self.cur_image = 0
        logger.info(f'Camera: Finished Preparing Image Series')
        self.start_time = time.time()

    @QtCore.pyqtSlot()
    def add_images_to_series(self):
        if self.cur_image == 0:
            logger.info('Thread ID during add images: '+str(int(QtCore.QThread.currentThreadId())))

        if self.stopflag is False:
            if self.cur_image + 1 < self.max_frame:
                images = self.camera.get_images_in_series()
                for image in images:
                    image = np.rot90(image)
                    self.sig_camera_frame.emit(image[0:self.x_pixels:self.camera_display_acquisition_subsampling,0:self.y_pixels:self.camera_display_acquisition_subsampling])
                    image = image.flatten()
                    self.xy_stack[self.cur_image*self.fsize:(self.cur_image+1)*self.fsize] = image
                    self.cur_image += 1

    @QtCore.pyqtSlot()
    def end_image_series(self):
        try:
            self.camera.close_image_series()
            del self.xy_stack
        except:
            pass

        self.end_time =  time.time()
        framerate = (self.cur_image + 1)/(self.end_time - self.start_time)
        logger.info(f'Camera: Framerate: {framerate}')
        self.sig_finished.emit()

    @QtCore.pyqtSlot()
    def snap_image(self):
        image = self.camera.get_image()
        image = np.rot90(image)

        timestr = time.strftime("%Y%m%d-%H%M%S")
        filename = timestr + '.tif'

        path = self.state['snap_folder']+'/'+filename

        self.sig_camera_frame.emit(image[0:self.x_pixels:self.camera_display_snap_subsampling,0:self.y_pixels:self.camera_display_snap_subsampling])

        tifffile.imsave(path, image, photometric='minisblack')

    @QtCore.pyqtSlot()
    def prepare_live(self):
        self.camera.initialize_live_mode()

        self.live_image_count = 0

        self.start_time = time.time()
        logger.info('Camera: Preparing Live Mode')
        logger.info('Thread ID during live: '+str(int(QtCore.QThread.currentThreadId())))

    @QtCore.pyqtSlot()
    def get_live_image(self):
        images = self.camera.get_live_image()

        for image in images:
            image = np.rot90(image)

            self.sig_camera_frame.emit(image[0:self.x_pixels:self.camera_display_live_subsampling,0:self.y_pixels:self.camera_display_live_subsampling])
            self.live_image_count += 1
            #self.sig_camera_status.emit(str(self.live_image_count))

    @QtCore.pyqtSlot()
    def end_live(self):
        self.camera.close_live_mode()
        self.end_time =  time.time()
        framerate = (self.live_image_count + 1)/(self.end_time - self.start_time)
        logger.info(f'Camera: Finished Live Mode: Framerate: {framerate}')

class mesoSPIM_GenericCamera(QtCore.QObject):
    ''' Generic mesoSPIM camera class meant for subclassing.'''

    def __init__(self, parent = None):
        super().__init__()
        self.parent = parent
        self.cfg = parent.cfg

        self.state = mesoSPIM_StateSingleton()

        self.stopflag = False

        self.x_pixels = self.cfg.camera_parameters['x_pixels']
        self.y_pixels = self.cfg.camera_parameters['y_pixels']
        self.x_pixel_size_in_microns = self.cfg.camera_parameters['x_pixel_size_in_microns']
        self.y_pixel_size_in_microns = self.cfg.camera_parameters['y_pixel_size_in_microns']

        self.camera_line_interval = self.cfg.startup['camera_line_interval']
        self.camera_exposure_time = self.cfg.startup['camera_exposure_time']

    def open_camera(self):
        pass

    def close_camera(self):
        pass

    def set_exposure_time(self, time):
        pass

    def set_line_interval(self, time):
        pass

    def initialize_image_series(self):
        pass

    def get_images_in_series(self):
        '''Should return a single numpy array'''
        pass

    def close_image_series(self):
        pass

    def get_image(self):
        '''Should return a single numpy array'''
        pass

    def initialize_live_mode(self):
        pass

    def get_live_image(self):
        pass

    def close_live_mode(self):
        pass

class mesoSPIM_DemoCamera(mesoSPIM_GenericCamera):

    def __init__(self, parent = None):
        super().__init__(parent)

        self.line = np.linspace(0,6*np.pi,self.x_pixels)
        self.line = 400*np.sin(self.line)+1200

        self.count = 0

    def open_camera(self):
        logger.info('Initialized Demo Camera')

    def close_camera(self):
        logger.info('Closed Demo Camera')

    def _create_random_image(self):
        data = np.array([np.roll(self.line, 4*i+self.count) for i in range(0, self.y_pixels)])
        data = data + np.random.normal(size=(self.x_pixels, self.y_pixels))*100
        self.count += 20
        return data

        # return np.random.randint(low=0, high=2**16, size=(self.x_pixels,self.y_pixels), dtype='l')

    def get_images_in_series(self):
        return [self._create_random_image()]

    def get_image(self):
        return self._create_random_image()

    def get_live_image(self):
        return [self._create_random_image()]

class mesoSPIM_HamamatsuCamera2(mesoSPIM_GenericCamera):
    def __init__(self, parent = None):
        super().__init__(parent)
        logger.info('Thread ID at Startup: '+str(int(QtCore.QThread.currentThreadId())))

    def open_camera(self):
        ''' Hamamatsu-specific code '''
        self.camera_id = self.cfg.camera_parameters['camera_id']

        from .devices.cameras.hamamatsu import hamamatsu_camera as cam
        # if self.cfg.camera == 'HamamatsuOrcaFlash':
        self.hcam = cam.HamamatsuCameraMR(camera_id=self.camera_id)
        ''' Debbuging information '''
        logger.info(f'Initialized Hamamatsu camera model: {self.hcam.getModelInfo(self.camera_id)}')

        ''' Ideally, the Hamamatsu Camera properties should be set in this order '''
        ''' mesoSPIM mode parameters '''
        self.hcam.setPropertyValue("sensor_mode", self.cfg.camera_parameters['sensor_mode'])

        self.hcam.setPropertyValue("defect_correct_mode", self.cfg.camera_parameters['defect_correct_mode'])
        self.hcam.setPropertyValue("exposure_time", self.camera_exposure_time)
        self.hcam.setPropertyValue("binning", self.cfg.camera_parameters['binning'])
        self.hcam.setPropertyValue("readout_speed", self.cfg.camera_parameters['readout_speed'])

        self.hcam.setPropertyValue("trigger_active", self.cfg.camera_parameters['trigger_active'])
        self.hcam.setPropertyValue("trigger_mode", self.cfg.camera_parameters['trigger_mode']) # it is unclear if this is the external lightsheeet mode - how to check this?
        self.hcam.setPropertyValue("trigger_polarity", self.cfg.camera_parameters['trigger_polarity']) # positive pulse
        self.hcam.setPropertyValue("trigger_source", self.cfg.camera_parameters['trigger_source']) # external
        self.hcam.setPropertyValue("internal_line_interval",self.camera_line_interval)

    def close_camera(self):
        self.hcam.shutdown()

    def set_camera_sensor_mode(self, mode):
        if mode == 'Area':
            self.hcam.setPropertyValue("sensor_mode", 1)
        elif mode == 'ASLM':
            self.hcam.setPropertyValue("sensor_mode", 12)
        else:
            print('Camera mode not supported')

    def set_exposure_time(self, time):
        self.hcam.setPropertyValue("exposure_time", time)

    def set_line_interval(self, time):
        self.hcam.setPropertyValue("internal_line_interval",self.camera_line_interval)

    def initialize_image_series(self):
        self.hcam.startAcquisition()

    def get_images_in_series(self):
        [frames, _] = self.hcam.getFrames()
        images = [np.reshape(aframe.getData(), (-1,2048)) for aframe in frames]
        return images

    def close_image_series(self):
        self.hcam.stopAcquisition()

    def get_image(self):
        [frames, _] = self.hcam.getFrames()
        images = [np.reshape(aframe.getData(), (-1,2048)) for aframe in frames]
        return images[0]

    def initialize_live_mode(self):
        self.hcam.setACQMode(mode = "run_till_abort")
        self.hcam.startAcquisition()

    def get_live_image(self):
        [frames, _] = self.hcam.getFrames()
        images = [np.reshape(aframe.getData(), (-1,2048)) for aframe in frames]
        return images

    def close_live_mode(self):
        self.hcam.stopAcquisition()

class mesoSPIM_PhotometricsCamera(mesoSPIM_GenericCamera):
    def __init__(self, parent = None):
        super().__init__(parent)
        logger.info('Thread ID at Startup: '+str(int(QtCore.QThread.currentThreadId())))

    def open_camera(self):
        from pyvcam import pvc
        from pyvcam import constants as const
        from pyvcam.camera import Camera

        self.const = const
        self.pvc = pvc

        pvc.init_pvcam()
        self.pvcam = [cam for cam in Camera.detect_camera()][0]

        self.pvcam.open()
        self.pvcam.speed_table_index = 0
        self.pvcam.exp_mode = "Ext Trig Internal"

        self.pvcam.set_param(param_id = self.const.PARAM_SCAN_MODE, value = 0)
        '''
        pvc.init_pvcam()
        self.cam = [cam for cam in Camera.detect_camera()][0]

        self.cam.open()
        self.cam.speed_table_index = 0
        self.cam.exp_mode = "Ext Trig Internal"

        self.cam.set_param(param_id = const.PARAM_SCAN_MODE, value = 0)

        self.cam.set_param(param_id = PARAM_SCAN_LINE_DELAY, value = 4)
        '''

    def close_camera(self):
        self.pvcam.close()
        self.pvc.uninit_pvcam()

    def get_image(self):
        '''Exposure time in ms'''
        return self.pvcam.get_frame(exp_time=self.camera_exposure_time*1000)

    def get_images_in_series(self):
        return [self.pvcam.get_frame(exp_time=self.camera_exposure_time*1000)]

    def get_live_image(self):
        return [self.pvcam.get_frame(exp_time=self.camera_exposure_time*1000)]

class mesoSPIM_HamamatsuCamera(QtCore.QObject):
    sig_camera_frame = QtCore.pyqtSignal(np.ndarray)
    sig_finished = QtCore.pyqtSignal()
    sig_update_gui_from_state = QtCore.pyqtSignal(bool)

    def __init__(self, parent = None):
        super().__init__()

        self.parent = parent
        self.cfg = parent.cfg

        self.state = mesoSPIM_StateSingleton()

        self.stopflag = False

        self.x_pixels = self.cfg.camera_parameters['x_pixels']
        self.y_pixels = self.cfg.camera_parameters['y_pixels']
        self.x_pixel_size_in_microns = self.cfg.camera_parameters['x_pixel_size_in_microns']
        self.y_pixel_size_in_microns = self.cfg.camera_parameters['y_pixel_size_in_microns']

        self.camera_line_interval = self.cfg.startup['camera_line_interval']
        self.camera_exposure_time = self.cfg.startup['camera_exposure_time']

        self.camera_display_live_subsampling = self.cfg.startup['camera_display_live_subsampling']
        self.camera_display_snap_subsampling = self.cfg.startup['camera_display_snap_subsampling']
        self.camera_display_acquisition_subsampling = self.cfg.startup['camera_display_acquisition_subsampling']

        ''' Wiring signals '''
        self.parent.sig_state_request.connect(self.state_request_handler)

        self.parent.sig_prepare_image_series.connect(self.prepare_image_series, type=3)
        self.parent.sig_add_images_to_image_series.connect(self.add_images_to_series)
        self.parent.sig_add_images_to_image_series_and_wait_until_done.connect(self.add_images_to_series, type=3)
        self.parent.sig_end_image_series.connect(self.end_image_series, type=3)

        self.parent.sig_prepare_live.connect(self.prepare_live, type = 3)
        self.parent.sig_get_live_image.connect(self.get_live_image)
        self.parent.sig_get_snap_image.connect(self.snap_image)
        self.parent.sig_end_live.connect(self.end_live, type=3)

        ''' Initialize camera '''

        self.open_camera()

        logger.info('Thread ID at Startup: '+str(int(QtCore.QThread.currentThreadId())))

    def __del__(self):
        self.close_camera()

    @QtCore.pyqtSlot(dict)
    def state_request_handler(self, dict):
        for key, value in zip(dict.keys(),dict.values()):
            # print('Camera Thread: State request: Key: ', key, ' Value: ', value)
            '''
            The request handling is done with exec() to write fewer lines of
            code.
            '''
            if key in ('camera_exposure_time',
                        'camera_line_interval',
                        'state',
                        'camera_display_live_subsampling',
                        'camera_display_snap_subsampling',
                        'camera_display_acquisition_subsampling'):
                exec('self.set_'+key+'(value)')
            # Log Thread ID during Live: just debugging code
            elif key == 'state':
                if value == 'live':
                    logger.info('Thread ID during live: '+str(int(QtCore.QThread.currentThreadId())))

    def open_camera(self):
        ''' Hamamatsu-specific code '''
        self.camera_id = self.cfg.camera_parameters['camera_id']

        from .devices.cameras.hamamatsu import hamamatsu_camera as cam
        # if self.cfg.camera == 'HamamatsuOrcaFlash':
        self.hcam = cam.HamamatsuCameraMR(camera_id=self.camera_id)
        ''' Debbuging information '''
        logger.info(f'Hamamatsu Camera model: {self.hcam.getModelInfo(self.camera_id)}')

        ''' Ideally, the Hamamatsu Camera properties should be set in this order '''
        ''' mesoSPIM mode parameters '''
        self.hcam.setPropertyValue("sensor_mode", self.cfg.camera_parameters['sensor_mode'])

        self.hcam.setPropertyValue("defect_correct_mode", self.cfg.camera_parameters['defect_correct_mode'])
        self.hcam.setPropertyValue("exposure_time", self.camera_exposure_time)
        self.hcam.setPropertyValue("binning", self.cfg.camera_parameters['binning'])
        self.hcam.setPropertyValue("readout_speed", self.cfg.camera_parameters['readout_speed'])

        self.hcam.setPropertyValue("trigger_active", self.cfg.camera_parameters['trigger_active'])
        self.hcam.setPropertyValue("trigger_mode", self.cfg.camera_parameters['trigger_mode']) # it is unclear if this is the external lightsheeet mode - how to check this?
        self.hcam.setPropertyValue("trigger_polarity", self.cfg.camera_parameters['trigger_polarity']) # positive pulse
        self.hcam.setPropertyValue("trigger_source", self.cfg.camera_parameters['trigger_source']) # external
        self.hcam.setPropertyValue("internal_line_interval",self.camera_line_interval)

    def close_camera(self):
        self.hcam.shutdown()

    def set_state(self, requested_state):
        pass

        # if requested_state == ('live' or 'run_selected_acquisition' or 'run_acquisition_list'):
        #     self.live()
        # elif requested_state == 'idle':
        #     self.stop()

    def open(self):
        pass

    def close(self):
        pass

    @QtCore.pyqtSlot()
    def stop(self):
        ''' Stops acquisition '''
        self.stopflag = True

    def set_camera_sensor_mode(self, mode):
        if mode == 'Area':
            self.hcam.setPropertyValue("sensor_mode", 1)
        elif mode == 'ASLM':
            self.hcam.setPropertyValue("sensor_mode", 12)
        else:
            print('Camera mode not supported')

    def set_camera_exposure_time(self, time):
        '''
        Sets the exposure time in seconds

        Args:
            time (float): exposure time to set
        '''
        self.camera_exposure_time = time
        self.hcam.setPropertyValue("exposure_time", time)
        self.sig_update_gui_from_state.emit(True)
        self.state['camera_exposure_time'] = time
        self.sig_update_gui_from_state.emit(False)

    def set_camera_line_interval(self, time):
        '''
        Sets the line interval in seconds

        Args:
            time (float): interval time to set
        '''
        self.camera_line_interval = time
        self.hcam.setPropertyValue("internal_line_interval",self.camera_line_interval)
        self.sig_update_gui_from_state.emit(True)
        self.state['camera_line_interval'] = time
        self.sig_update_gui_from_state.emit(False)

    def set_camera_display_live_subsampling(self, factor):
        self.camera_display_live_subsampling = factor

    def set_camera_display_snap_subsampling(self, factor):
        self.camera_display_snap_subsampling = factor

    def set_camera_display_acquisition_subsampling(self, factor):
        self.camera_display_acquisition_subsampling = factor

    @QtCore.pyqtSlot(Acquisition)
    def prepare_image_series(self, acq):
        '''
        Row is a row in a AcquisitionList
        '''
        logger.info('Camera: Preparing Image Series')
        #print('Cam: Preparing Image Series')
        self.stopflag = False

        self.path = acq['folder']+'/'+acq['filename']

        logger.info(f'Camera: Save path: {self.path}')
        self.z_start = acq['z_start']
        self.z_end = acq['z_end']
        self.z_stepsize = acq['z_step']
        self.max_frame = acq.get_image_count()

        self.fsize = 2048*2048

        self.xy_stack = np.memmap(self.path, mode = "write", dtype = np.uint16, shape = self.fsize * self.max_frame)
        # self.xy_stack_tif = tf.memmap(tif_filename, shape=(self.max_frame, 2048, 2048), dtype = np.uint16)
        # self.xz_stack = np.memmap(self.path[:-4]+'xz.raw', mode = "write", dtype = np.uint16, shape = 2048 * self.max_frame * 2048)
        # self.yz_stack = np.memmap(self.path[:-4]+'yz.raw', mode = "write", dtype = np.uint16, shape = 2048 * self.max_frame * 2048)

        self.hcam.startAcquisition()
        self.cur_image = 0
        logger.info(f'Camera: Finished Preparing Image Series')
        #print('Cam: Finished Preparing Image Series')
        self.start_time = time.time()

    @QtCore.pyqtSlot()
    def add_images_to_series(self):
        if self.cur_image == 0:
            logger.info('Thread ID during add images: '+str(int(QtCore.QThread.currentThreadId())))

        # QtWidgets.QApplication.processEvents(QtCore.QEventLoop.AllEvents, 1)
        if self.stopflag is False:
            # print('Camera: Adding images started')
            if self.cur_image + 1 < self.max_frame:
                [frames, _] = self.hcam.getFrames()

                # for aframe in frames:

                #     image = aframe.getData()
                #     self.xy_stack[self.cur_image*self.fsize:(self.cur_image+1)*self.fsize] = image

                #     image = np.reshape(image, (-1, 2048))
                #     # image = np.rot90(image)
                #     self.sig_camera_frame.emit(image)
                #     # ''' Creating a 512x512 subimage '''
                #     # if self.cur_image % 20 == 0:
                #     #     subimage = image[0:2048:4,0:2048:4]
                #     #     self.sig_camera_frame.emit(subimage)
                #     # image = image.flatten()
                #     print('Done with image: #', self.cur_image)
                #     self.cur_image += 1
                num_frames = len(frames)
                for aframe in frames:

                    image = aframe.getData()

                    image = np.reshape(image, (-1, 2048))
                    image = np.rot90(image)

                    # if (num_frames == 1) and (self.cur_image % 2 == 0):
                    #     subimage = image[0:2048:4,0:2048:4]
                    #     self.sig_camera_frame.emit(subimage)

                    self.sig_camera_frame.emit(image[0:2048:self.camera_display_acquisition_subsampling,0:2048:self.camera_display_acquisition_subsampling])
                    image = image.flatten()
                    self.xy_stack[self.cur_image*self.fsize:(self.cur_image+1)*self.fsize] = image

                    #print('Done with image: #', self.cur_image)
                    self.cur_image += 1

            #print('Camera: Adding images ended')
        else:
            pass
            #print('Camera: Acquisition stop requested...')

    @QtCore.pyqtSlot()
    def end_image_series(self):
        try:
            self.hcam.stopAcquisition()
            del self.xy_stack

        except:
            pass
            #print('Camera: Error when finishing acquisition.')

        self.end_time =  time.time()
        framerate = (self.cur_image + 1)/(self.end_time - self.start_time)
        logger.info(f'Camera: Framerate: {framerate}')
        self.sig_finished.emit()

    @QtCore.pyqtSlot()
    def snap_image(self):
        [frames, _] = self.hcam.getFrames()

        for aframe in frames:
            image = aframe.getData()
            image = np.reshape(image, (-1, 2048))
            image = np.rot90(image)

            timestr = time.strftime("%Y%m%d-%H%M%S")
            filename = timestr + '.tif'

            path = self.state['snap_folder']+'/'+filename

            self.sig_camera_frame.emit(image)

            tifffile.imsave(path, image, photometric='minisblack')

    @QtCore.pyqtSlot()
    def prepare_live(self):
        self.hcam.setACQMode(mode = "run_till_abort")
        self.hcam.startAcquisition()

        self.live_image_count = 0

        self.start_time = time.time()
        logger.info('Camera: Preparing Live Mode')
        logger.info('Thread ID during live: '+str(int(QtCore.QThread.currentThreadId())))

    @QtCore.pyqtSlot()
    def get_live_image(self):
        [frames, _] = self.hcam.getFrames()

        for aframe in frames:
            image = aframe.getData()
            image = np.reshape(image, (-1, 2048))
            image = np.rot90(image)

            self.sig_camera_frame.emit(image[0:2048:self.camera_display_live_subsampling,0:2048:self.camera_display_live_subsampling])
            self.live_image_count += 1
            #self.sig_camera_status.emit(str(self.live_image_count))

    @QtCore.pyqtSlot()
    def end_live(self):
        self.hcam.stopAcquisition()
        self.end_time =  time.time()
        framerate = (self.live_image_count + 1)/(self.end_time - self.start_time)
        logger.info(f'Camera: Finished Live Mode: Framerate: {framerate}')
