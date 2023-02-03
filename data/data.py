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
NOTE_FIELD = 'notes'
BATTERY_FIELD = 'battery_state'
BATTERY_CHARGING = 'charging'


class FullSensorData:
    def __init__(self):
        """
        stamp,yaw,pitch,roll,rotation_rate_x,rotation_rate_y,rotation_rate_z,user_acceleration_x,
            user_acceleration_y,user_acceleration_z,latitude,longitude,altitude,course,speed,
            horizontal_accuracy,vertical_accuracy,battery_state,user_activity_label,is_gps_valid
        dt,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,s,s,s

        Errands, Exercise, Hobby, Housework, Hygiene, Mealtime, Other, Relax, Sleep,
        Socialize, Travel, Work
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
        self.ann_set = set()
        self.ann_list = list()
        self.ann_y = dict()
        self.ann_colors = dict()
        self.color_map = list()
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
        self.ann_set.add(annotation)
        self.update_ann_list()
        return

    def annotate_given_window(self, data_window: SingleDataWindow):
        self.data_has_changed = True
        for i in range(data_window.i_start, data_window.i_last + 1):
            self.sensor_data[i][LABEL_FIELD] = data_window.label
        self.ann_set.add(data_window.label)
        self.update_ann_list()
        return

    def add_note(self, msg: str):
        self.data_has_changed = True
        i = self.index + self.sensor_window - 1
        self.sensor_data[i][NOTE_FIELD] = msg
        if msg == '':
            self.sensor_data[i][NOTE_FIELD] = None
        return

    def get_label_text(self) -> str:
        msg = ''
        labels = list()
        i = self.index + self.sensor_window - 1
        labels.append('> {}  {}\n'.format(str(self.sensor_data[i]['stamp']),
                                          self.sensor_data[i][LABEL_FIELD]))
        labels.append('\n')
        current_label = str(self.sensor_data[i][LABEL_FIELD])
        added_dots = False
        while i > 0 and len(labels) < 10:
            if str(self.sensor_data[i][LABEL_FIELD]) != current_label:
                label = self.sensor_data[i][LABEL_FIELD]
                if label is None:
                    label = ''
                labels.append('{}  {}\n'.format(str(self.sensor_data[i]['stamp']), label))
                current_label = str(self.sensor_data[i][LABEL_FIELD])
                added_dots = False
            elif not added_dots:
                added_dots = True
                labels.append('    ...    \n')
            i -= 1

        i = self.index + self.sensor_window - 1
        labels.reverse()
        labels.append('\n')
        current_label = str(self.sensor_data[i][LABEL_FIELD])
        added_dots = False
        while i < self.data_size and len(labels) < 20:
            if str(self.sensor_data[i][LABEL_FIELD]) != current_label:
                label = self.sensor_data[i][LABEL_FIELD]
                if label is None:
                    label = ''
                labels.append('{}  {}\n'.format(str(self.sensor_data[i]['stamp']), label))
                current_label = str(self.sensor_data[i][LABEL_FIELD])
                added_dots = False
            elif not added_dots:
                added_dots = True
                labels.append('    ...    \n')
            i += 1

        for line in labels:
            msg += line
        return msg

    def get_given_label_text(self, data_window: SingleDataWindow) -> str:
        msg = ''
        labels = list()
        i = data_window.i_start
        labels.append('> {}  {}\n'.format(str(self.sensor_data[i]['stamp']),
                                          self.sensor_data[i][LABEL_FIELD]))
        labels.append('\n')
        current_label = str(self.sensor_data[i][LABEL_FIELD])
        added_dots = False
        while i > 0 and len(labels) < 10:
            if str(self.sensor_data[i][LABEL_FIELD]) != current_label:
                label = self.sensor_data[i][LABEL_FIELD]
                if label is None:
                    label = ''
                labels.append('{}  {}\n'.format(str(self.sensor_data[i]['stamp']), label))
                current_label = str(self.sensor_data[i][LABEL_FIELD])
                added_dots = False
            elif not added_dots:
                added_dots = True
                labels.append('    ...    \n')
            i -= 1

        labels.reverse()
        i = data_window.i_last
        labels.append('> {}  {}\n'.format(str(self.sensor_data[i]['stamp']),
                                          self.sensor_data[i][LABEL_FIELD]))
        labels.append('\n')
        added_dots = False
        while i < self.data_size and len(labels) < 20:
            if str(self.sensor_data[i][LABEL_FIELD]) != current_label:
                label = self.sensor_data[i][LABEL_FIELD]
                if label is None:
                    label = ''
                labels.append('{}  {}\n'.format(str(self.sensor_data[i]['stamp']), label))
                current_label = str(self.sensor_data[i][LABEL_FIELD])
                added_dots = False
            elif not added_dots:
                added_dots = True
                labels.append('    ...    \n')
            i += 1

        for line in labels:
            msg += line
        return msg

    def plot_given_window(self, data_window: SingleDataWindow, axis1, axis2, axis3, axis4):
        # Save the current settings to restore after plotting.
        tmp_sensor_window = self.sensor_window
        tmp_index = self.index
        self.index = data_window.i_start
        self.sensor_window = abs(data_window.i_last - data_window.i_start)

        # Now call the plot function.
        self.plot_sensors(axis1=axis1,
                          axis2=axis2,
                          axis3=axis3,
                          axis4=axis4)

        # Restore the settings.
        self.sensor_window = tmp_sensor_window
        self.index = tmp_index
        return

    def plot_sensors(self, axis1, axis2, axis3, axis4):
        x = np.array(list(range(self.sensor_window)))
        index_range = list(range(self.index, self.index + self.sensor_window))
        # Annotations or notes.
        ann_x = list()
        ann_y = list()
        ann_color = list()
        ann_found = False
        note_x = list()
        note_y = list()
        note_found = False
        batt_x = list()
        batt_y = list()
        batt_found = False
        zero = list()
        for j, i in enumerate(index_range):
            zero.append(-0.5)
            if self.sensor_data[i][LABEL_FIELD] is not None:
                ann_x.append(j)
                ann_y.append(self.ann_y[self.sensor_data[i][LABEL_FIELD]])
                ann_color.append(self.ann_colors[self.sensor_data[i][LABEL_FIELD]])
                ann_found = True
            if self.sensor_data[i][NOTE_FIELD] is not None:
                note_x.append(j)
                note_y.append(-1)
                note_found = True
            if self.sensor_data[i][BATTERY_FIELD] is not None:
                if self.sensor_data[i][BATTERY_FIELD] == BATTERY_CHARGING:
                    batt_x.append(j)
                    batt_y.append(-0.5)
                    batt_found = True
        axis1.scatter(x, np.array(zero), color='white', marker='.')
        if ann_found:
            axis1.scatter(ann_x, ann_y, s=80, c=ann_color, marker='|')
        for key in list(self.ann_y.keys()):
            axis1.annotate(key, xy=(0, self.ann_y[key]), color=self.ann_colors[key])
        if note_found:
            axis1.scatter(note_x, note_y, s=80, c='green', marker='^')
        if batt_found:
            axis1.scatter(batt_x, batt_y, s=5, c='red', marker='>')
        axis1.autoscale_view()
        axis1.set_ylabel(ylabel='labels')
        axis1.set_ylim(bottom=-1, top=len(self.ann_colors))

        # yaw, pitch, roll
        yaw = np.array([self.sensor_data[i]['yaw'] for i in index_range])
        pitch = np.array([self.sensor_data[i]['pitch'] for i in index_range])
        roll = np.array([self.sensor_data[i]['roll'] for i in index_range])
        axis2.plot(x, yaw, label='yaw')
        axis2.plot(x, pitch, label='pitch')
        axis2.plot(x, roll, label='roll')
        self.adjust_axes(axis=axis2,
                         label='yaw/pitch/roll')

        # rotation_rate_x, rotation_rate_y, rotation_rate_z
        rotation_rate_x = np.array([self.sensor_data[i]['rotation_rate_x'] for i in index_range])
        rotation_rate_y = np.array([self.sensor_data[i]['rotation_rate_y'] for i in index_range])
        rotation_rate_z = np.array([self.sensor_data[i]['rotation_rate_z'] for i in index_range])
        axis3.plot(x, rotation_rate_x, label='x')
        axis3.plot(x, rotation_rate_y, label='y')
        axis3.plot(x, rotation_rate_z, label='z')
        self.adjust_axes(axis=axis3,
                         label='rotation rate')

        # user_acceleration_x, user_acceleration_y, user_acceleration_z
        user_acc_x = np.array([self.sensor_data[i]['user_acceleration_x'] for i in index_range])
        user_acc_y = np.array([self.sensor_data[i]['user_acceleration_y'] for i in index_range])
        user_acc_z = np.array([self.sensor_data[i]['user_acceleration_z'] for i in index_range])
        axis4.plot(x, user_acc_x, label='x')
        axis4.plot(x, user_acc_y, label='y')
        axis4.plot(x, user_acc_z, label='z')
        self.adjust_axes(axis=axis4,
                         label='user acceleration')
        axis4.set_xlabel(xlabel='{}  ->  {}  (NOW)'.format(
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

    def update_ann_list(self):
        # This assumes you have added any possible new value to the set already.
        del self.ann_list
        self.ann_list = list(self.ann_set)
        self.ann_list.sort()
        del self.ann_colors
        self.ann_colors = dict()
        del self.ann_y
        self.ann_y = dict()
        ann_len = len(self.ann_list) - 1
        for i, ann in enumerate(self.ann_list):
            self.ann_colors[ann] = self.color_map[i % len(self.color_map)]
            self.ann_y[ann] = i
        return

    def load_data(self, filename: str, gps_data: WatchGPSData, update_callback=None,
                  done_callback=None):
        fsize = -1
        with open(filename, 'r') as mdata:
            for line in mdata:
                fsize += 1
        del self.sensor_data
        self.sensor_data = list()
        del self.ann_set
        self.ann_set = set()
        del self.ann_list
        self.ann_list = list()
        del self.ann_colors
        self.ann_colors = dict()
        del self.ann_y
        self.ann_y = dict()
        self.has_data = False
        self.data_has_changed = False
        self.index = 0
        self.data_size = 0
        self.sensor_window = DEFAULT_SENSOR_WINDOW
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
            has_notes = True
            if NOTE_FIELD not in self.fields:
                has_notes = False
                self.fields[NOTE_FIELD] = 's'
            count = 0
            cur_lat = -1.0
            cur_lon = -1.0
            for row in mdata.rows_dict:
                if (count % 1000) == 0:
                    msg = 'Loading file...\n'
                    percent = float(int(1000.0 * float(count) / float(fsize))) / 10.0
                    msg += '{}% complete. {} of {} rows loaded\n'.format(percent, count, fsize)
                    msg += 'At stamp: {}'.format(str(row['stamp']))
                    if update_callback is not None:
                        update_callback(msg)
                        time.sleep(0.001)
                if not has_label:
                    row[LABEL_FIELD] = None
                if not has_gps_valid:
                    row[GPS_VALID_FIELD] = GPS_VALID_DICT[DEFAULT_IS_VALID]
                if not has_notes:
                    row[NOTE_FIELD] = None

                if row[LABEL_FIELD] is not None:
                    self.ann_set.add(row[LABEL_FIELD])
                    # print(str(row['stamp']), row[LABEL_FIELD])

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

        self.update_ann_list()
        print(self.ann_list)
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
