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
import copy
import datetime
import time
from collections import OrderedDict

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
        self.sensor_window = 100
        self.fields = None
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
        if (self.index + self.sensor_window + 1) < self.data_size:
            self.sensor_window += 1
            action = True
        return action

    def decrease_window_size(self) -> bool:
        action = False
        if (self.sensor_window - 1) >= 1:
            self.sensor_window -= 1
            action = True
        return action

    def step_forward(self) -> bool:
        action = False
        if (self.index + self.sensor_window + 1) < self.data_size:
            self.index += 1
            action = True
        return action

    def step_backward(self) -> bool:
        action = False
        if (self.index - 1) >= 0:
            self.index -= 1
            action = True
        return action

    def goto_index(self, clicked_float: float):
        if 0.0 <= clicked_float <= 1.0:
            self.index = int(clicked_float * self.data_size)
        return

    def annotate_window(self, annotation: str):
        self.data_has_changed = True
        for i in range(self.index, self.index + self.sensor_window):
            self.sensor_data[i][LABEL_FIELD] = annotation
        return

    def plot_sensors(self, axis):
        return

    def load_data(self, filename: str, gps_data: WatchGPSData, update_callback=None,
                  done_callback=None):
        del self.sensor_data
        self.sensor_data = list()
        self.has_data = False
        self.data_has_changed = False
        self.index = 0
        self.data_size = 0
        self.sensor_window = 100
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
                if (count % 500) == 0:
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

        if len(self.sensor_data) > 0:
            gps_data.load_data_end()
            self.data_size = len(self.sensor_data)
            self.has_data = True
            self.data_has_changed = False

        if done_callback is not None:
            done_callback()
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
