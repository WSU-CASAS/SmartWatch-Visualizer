# *****************************************************************************#
# **
# **  Smart Watch Visualizer
# **
# **    Brian L. Thomas, 2023
# **
# ** Tools by the Center for Advanced Studies in Adaptive Systems at the
# **  School of Electrical Engineering and Computer Science at
# **  Washington State University
# **
# ** Copyright Brian L. Thomas, 2023
# **
# ** All rights reserved
# ** Modification, distribution, and sale of this work is prohibited without
# **  permission from Washington State University
# **
# ** Contact: Brian L. Thomas (bthomas1@wsu.edu)
# *****************************************************************************#
from .mobile_al_data import MobileData
from .gps import WatchGPSData
from .data import FullSensorData
import copy
import datetime
import os

MODE_GPS = 'gps'
MODE_SENSORS = 'sensors'
VALID_MODES = list([MODE_GPS, MODE_SENSORS])


class WatchData:
    def __init__(self):
        self.mode = MODE_SENSORS
        self.has_any_data = False
        self.gps_data = WatchGPSData()
        self.full_data = FullSensorData()
        return

    def set_mode(self, mode: str):
        if mode in VALID_MODES:
            self.mode = mode
        return

    def has_data(self) -> bool:
        return self.has_any_data

    def has_gps_data(self) -> bool:
        return self.gps_data.has_data

    def has_sensors_data(self) -> bool:
        return self.full_data.has_data

    def index(self) -> int:
        i = 0
        if self.mode == MODE_GPS:
            i = self.gps_data.index
        elif self.mode == MODE_SENSORS:
            i = self.full_data.index
        return i

    def data_size(self) -> int:
        i = 20
        if self.mode == MODE_GPS:
            i = self.gps_data.data_size - self.gps_data.gps_window
        elif self.mode == MODE_SENSORS:
            i = self.full_data.data_size - self.full_data.sensor_window
        return i

    def get_first_stamp(self) -> str:
        msg = '...'
        if self.mode == MODE_GPS:
            msg = self.gps_data.get_first_stamp()
        elif self.mode == MODE_SENSORS:
            msg = self.full_data.get_first_stamp()
        return msg

    def get_current_stamp(self) -> str:
        msg = '...'
        if self.mode == MODE_GPS:
            msg = self.gps_data.get_current_stamp()
        elif self.mode == MODE_SENSORS:
            msg = self.full_data.get_current_stamp()
        return msg

    def get_last_stamp(self) -> str:
        msg = '...'
        if self.mode == MODE_GPS:
            msg = self.gps_data.get_last_stamp()
        elif self.mode == MODE_SENSORS:
            msg = self.full_data.get_last_stamp()
        return msg

    def increase_window_size(self) -> bool:
        action = False
        if self.mode == MODE_GPS:
            action = self.gps_data.increase_window_size()
        elif self.mode == MODE_SENSORS:
            action = self.full_data.increase_window_size()
        return action

    def decrease_window_size(self) -> bool:
        action = False
        if self.mode == MODE_GPS:
            action = self.gps_data.decrease_window_size()
        elif self.mode == MODE_SENSORS:
            action = self.full_data.decrease_window_size()
        return action

    def step_forward(self) -> bool:
        action = False
        if self.mode == MODE_GPS:
            action = self.gps_data.step_forward()
        elif self.mode == MODE_SENSORS:
            action = self.full_data.step_forward()
        return action

    def step_backward(self) -> bool:
        action = False
        if self.mode == MODE_GPS:
            action = self.gps_data.step_backward()
        elif self.mode == MODE_SENSORS:
            action = self.full_data.step_backward()
        return action

    def goto_index(self, clicked_float: float):
        if self.mode == MODE_GPS:
            self.gps_data.goto_index(clicked_float=clicked_float)
        elif self.mode == MODE_SENSORS:
            self.full_data.goto_index(clicked_float=clicked_float)
        return

    def mark_window_invalid(self):
        if self.mode == MODE_GPS:
            self.gps_data.mark_window_invalid()
        return

    def mark_window_valid(self):
        if self.mode == MODE_GPS:
            self.gps_data.mark_window_valid()
        return

    def annotate_window(self, annotation: str):
        if self.mode == MODE_SENSORS:
            self.full_data.annotate_window(annotation=annotation)
        return

    def plot_gps(self, axis):
        if self.mode == MODE_GPS:
            self.gps_data.plot_gps(axis=axis)
        return

    def plot_sensors(self, axis1, axis2, axis3):
        if self.mode == MODE_SENSORS:
            self.full_data.plot_sensors(axis1=axis1,
                                        axis2=axis2,
                                        axis3=axis3)
        return

    def load_data(self, filename: str, update_callback=None, done_callback=None):
        self.has_any_data = False
        self.full_data.load_data(filename=filename,
                                 gps_data=self.gps_data,
                                 update_callback=update_callback,
                                 done_callback=done_callback)
        if self.gps_data.has_data or self.full_data.has_data:
            self.has_any_data = True
        return

    def save_data(self, filename: str, update_callback=None, done_callback=None):
        self.full_data.merge_data_changes(gps_data=self.gps_data,
                                          update_callback=update_callback)
        self.full_data.save_data(filename=filename,
                                 update_callback=update_callback,
                                 done_callback=done_callback)
        return
