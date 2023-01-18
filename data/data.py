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
from .gps import GPSData
from .config import VizConfig
from .annotate import SingleDataWindow
import copy
import datetime
import time
import numpy as np
from collections import OrderedDict

DEFAULT_SENSOR_WINDOW = 500
DEFAULT_IS_VALID = True
GPS_VALID_FIELD = 'is_gps_valid'
GPS_VALID_DICT = dict({'0': False,
                       False: '0',
                       '1': True,
                       True: '1'})
LABEL_FIELD = 'user_activity_label'


class FullSensorData:
    def __init__(self):
        """
        stamp,yaw,pitch,roll,rotation_rate_x,rotation_rate_y,rotation_rate_z,user_acceleration_x,
            user_acceleration_y,user_acceleration_z,latitude,longitude,altitude,course,speed,
            horizontal_accuracy,vertical_accuracy,battery_state,user_activity_label,is_gps_valid
        dt,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,s,s,s
        """
        self.has_data = False
        self.data_has_changed = False
        self.index = 0
        self.data_size = 0
        self.sensor_data = list()
        self.sensor_window = DEFAULT_SENSOR_WINDOW
        self.fields = None
        self.window_size_adj_rate = 10
        self.step_delta_rate = 10
        return

    def update_config(self, wconfig: VizConfig):
        self.sensor_window = wconfig.sensors_window_size
        self.window_size_adj_rate = wconfig.sensors_win_size_adj_rate
        self.step_delta_rate = wconfig.sensors_step_delta_rate

        # Apply critical logic to window sizes.
        self.apply_window_variable_logic()

        # Save any changes back to the config object.
        self.set_config_obj(wconfig=wconfig)
        return

    def apply_window_variable_logic(self):
        if self.has_data:
            if self.data_size < self.sensor_window:
                self.sensor_window = self.data_size
            if self.data_size < self.window_size_adj_rate:
                self.window_size_adj_rate = int(self.data_size / 2)
            if self.data_size < self.step_delta_rate:
                self.step_delta_rate = int(self.data_size / 2)
        return

    def set_config_obj(self, wconfig: VizConfig):
        wconfig.sensors_window_size = self.sensor_window
        wconfig.sensors_win_size_adj_rate = self.window_size_adj_rate
        wconfig.sensors_step_delta_rate = self.step_delta_rate
        return

    def get_first_stamp(self) -> str:
        msg = '...'
        if self.has_data:
            msg = str(self.sensor_data[self.sensor_window - 1]['stamp'])
        return msg

    def get_current_stamp(self) -> str:
        msg = '...'
        if self.has_data:
            msg = str(self.sensor_data[self.index + self.sensor_window - 1]['stamp'])
        return msg

    def get_last_stamp(self) -> str:
        msg = '...'
        if self.has_data:
            msg = str(self.sensor_data[-1]['stamp'])
        return msg

    def increase_window_size(self) -> bool:
        action = False
        if (self.index + self.sensor_window + self.window_size_adj_rate) <= self.data_size:
            self.sensor_window += self.window_size_adj_rate
            action = True
        return action

    def decrease_window_size(self) -> bool:
        action = False
        if (self.sensor_window - self.window_size_adj_rate) >= 1:
            self.sensor_window -= self.window_size_adj_rate
            action = True
        return action

    def step_forward(self) -> bool:
        action = False
        if (self.index + self.sensor_window + self.step_delta_rate) <= self.data_size:
            self.index += self.step_delta_rate
            action = True
        return action

    def step_backward(self) -> bool:
        action = False
        if (self.index - self.step_delta_rate) >= 0:
            self.index -= self.step_delta_rate
            action = True
        return action

    def goto_index(self, clicked_float: float):
        if 0.0 <= clicked_float <= 1.0:
            self.index = int(clicked_float * (self.data_size - self.sensor_window))
        return

    def annotate_window(self, annotation: str):
        self.data_has_changed = True
        for i in range(self.index, self.index + self.sensor_window):
            self.sensor_data[i][LABEL_FIELD] = annotation
        return

    def annotate_given_window(self, data_window: SingleDataWindow):
        self.data_has_changed = True
        for i in range(data_window.i_start, data_window.i_last + 1):
            self.sensor_data[i][LABEL_FIELD] = data_window.label
        return

    def plot_given_window(self, data_window: SingleDataWindow, axis1, axis2, axis3):
        # Save the current settings to restore after plotting.
        tmp_sensor_window = self.sensor_window
        tmp_index = self.index
        self.index = data_window.i_start
        self.sensor_window = abs(data_window.i_last - data_window.i_start)

        # Now call the plot function.
        self.plot_sensors(axis1=axis1,
                          axis2=axis2,
                          axis3=axis3)

        # Restore the settings.
        self.sensor_window = tmp_sensor_window
        self.index = tmp_index
        return

    def plot_sensors(self, axis1, axis2, axis3):
        x = np.array(list(range(self.sensor_window)))
        index_range = list(range(self.index, self.index + self.sensor_window))
        # yaw, pitch, roll
        yaw = np.array([self.sensor_data[i]['yaw'] for i in index_range])
        pitch = np.array([self.sensor_data[i]['pitch'] for i in index_range])
        roll = np.array([self.sensor_data[i]['roll'] for i in index_range])
        axis1.plot(x, yaw, label='yaw')
        axis1.plot(x, pitch, label='pitch')
        axis1.plot(x, roll, label='roll')
        self.adjust_axes(axis=axis1,
                         label='yaw/pitch/roll')

        # rotation_rate_x, rotation_rate_y, rotation_rate_z
        rotation_rate_x = np.array([self.sensor_data[i]['rotation_rate_x'] for i in index_range])
        rotation_rate_y = np.array([self.sensor_data[i]['rotation_rate_y'] for i in index_range])
        rotation_rate_z = np.array([self.sensor_data[i]['rotation_rate_z'] for i in index_range])
        axis2.plot(x, rotation_rate_x, label='x')
        axis2.plot(x, rotation_rate_y, label='y')
        axis2.plot(x, rotation_rate_z, label='z')
        self.adjust_axes(axis=axis2,
                         label='rotation rate')

        # user_acceleration_x, user_acceleration_y, user_acceleration_z
        user_acc_x = np.array([self.sensor_data[i]['user_acceleration_x'] for i in index_range])
        user_acc_y = np.array([self.sensor_data[i]['user_acceleration_y'] for i in index_range])
        user_acc_z = np.array([self.sensor_data[i]['user_acceleration_z'] for i in index_range])
        axis3.plot(x, user_acc_x, label='x')
        axis3.plot(x, user_acc_y, label='y')
        axis3.plot(x, user_acc_z, label='z')
        self.adjust_axes(axis=axis3,
                         label='user acceleration')
        axis3.set_xlabel(xlabel='{}  ->  {}  (NOW)'.format(
            str(self.sensor_data[self.index]['stamp']),
            str(self.sensor_data[self.index + self.sensor_window - 1]['stamp'])))
        return

    def adjust_axes(self, axis, label):
        # This adjusts an axis and makes the most it will zoom in to be -1.0 to 1.0.
        axis.autoscale_view()
        bottom, top = axis.get_ylim()
        axis.set_ylim(bottom=min([bottom, -1.0]),
                      top=max(top, 1.0))
        axis.set_ylabel(ylabel=label)
        axis.legend(loc='upper left')
        return

    def load_data(self, filename: str, gps_data: WatchGPSData, update_callback=None,
                  done_callback=None):
        del self.sensor_data
        self.sensor_data = list()
        self.has_data = False
        self.data_has_changed = False
        self.index = 0
        self.data_size = 0
        self.sensor_window = DEFAULT_SENSOR_WINDOW
        labels = set()
        gps_data.load_data_init()
        with MobileData(filename, 'r') as mdata:
            del self.fields
            self.fields = copy.deepcopy(mdata.fields)
            has_label = True
            if LABEL_FIELD not in self.fields:
                has_label = False
                self.fields[LABEL_FIELD] = 's'
            has_gps_valid = True
            if GPS_VALID_FIELD not in self.fields:
                has_gps_valid = False
                self.fields[GPS_VALID_FIELD] = 's'
            count = 0
            cur_lat = -1.0
            cur_lon = -1.0
            for row in mdata.rows_dict:
                if (count % 1000) == 0:
                    msg = 'Loading file...\n'
                    msg += '{} rows loaded\n'.format(count)
                    msg += 'At stamp: {}'.format(str(row['stamp']))
                    if update_callback is not None:
                        update_callback(msg)
                        time.sleep(0.001)
                if not has_label:
                    row[LABEL_FIELD] = None
                if not has_gps_valid:
                    row[GPS_VALID_FIELD] = GPS_VALID_DICT[DEFAULT_IS_VALID]

                labels.add(row[LABEL_FIELD])
                if row[LABEL_FIELD] is not None:
                    print(str(row['stamp']), row[LABEL_FIELD])

                # Add copy of row to our sensor data.
                self.sensor_data.append(copy.deepcopy(row))

                # Add or update GPS data if it passes logic checks.
                if row['latitude'] is not None and row['longitude'] is not None:
                    if row['latitude'] != cur_lat or row['longitude'] != cur_lon:
                        gps_data.gps_data.append(
                            GPSData(longitude=row['longitude'],
                                    latitude=row['latitude'],
                                    start_stamp=row['stamp'],
                                    last_stamp=row['stamp'],
                                    count=1,
                                    is_valid=GPS_VALID_DICT[row[GPS_VALID_FIELD]],
                                    first_index=count,
                                    last_index=count))
                        gps_data.has_data = True
                        cur_lat = row['latitude']
                        cur_lon = row['longitude']
                    elif gps_data.has_data:
                        gps_data.gps_data[-1].count += 1
                        gps_data.gps_data[-1].last_stamp = copy.deepcopy(row['stamp'])
                        gps_data.gps_data[-1].last_index = count
                count += 1

        print(labels)
        if len(self.sensor_data) > 0:
            gps_data.load_data_end()
            self.data_size = len(self.sensor_data)
            self.has_data = True
            self.data_has_changed = False
            self.apply_window_variable_logic()
        return

    def merge_data_changes(self, gps_data: WatchGPSData, update_callback=None):
        if not gps_data.data_has_changed:
            print('No changes to GPS labels, nothing to merge!')
        else:
            self.data_has_changed = True
            for gps_row in gps_data.gps_data:
                msg = 'Merging GPS data changes to Sensor data...\n'
                percent = float(int(1000.0 * gps_row.first_index / self.data_size)) / 10.0
                msg += 'At {}% of data.\n'.format(percent)
                msg += '{}'.format(str(gps_row.start_stamp))
                update_callback(msg)
                for i in range(gps_row.first_index, gps_row.last_index + 1):
                    self.sensor_data[i][GPS_VALID_FIELD] = GPS_VALID_DICT[gps_row.is_valid]
            gps_data.data_has_changed = False
        return

    def save_data(self, filename: str, update_callback=None, done_callback=None):
        if not self.data_has_changed:
            print('No changes to our data, nothing to save!')
        else:
            with MobileData(filename, 'w') as mdata:
                mdata.set_fields(fields=self.fields)
                mdata.write_headers()

                count = 0
                for row in self.sensor_data:
                    if (count % 500) == 0:
                        msg = 'Saving to data file...\n'
                        percent = float(int(1000.0 * count / self.data_size)) / 10.0
                        msg += 'At {}% of the data...'.format(percent)
                        update_callback(msg)
                    mdata.write_row_dict(vals_dict=row)
                    count += 1

            self.data_has_changed = False

        if done_callback is not None:
            done_callback()
        return
