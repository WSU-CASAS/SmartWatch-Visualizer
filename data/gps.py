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
import copy
import datetime
import os
import numpy as np
import pandas as pd
import geopandas as gpd
import contextily as cx
from shapely.geometry import Point, LineString
import matplotlib.pyplot as plt
from .config import VizConfig

# plt.style.use('ggplot')
# plt.rcParams.update({'font.size': 16,
#                      'axes.labelweight': 'bold',
#                      'figure.figsize': (6, 6),
#                      'axes.edgecolor': '0.2'})
cx.set_cache_dir(path='data/contextily_cache')


class GPSData:
    def __init__(self, longitude: float, latitude: float, start_stamp: datetime.datetime,
                 last_stamp: datetime.datetime, count: int, is_valid: bool, first_index: int,
                 last_index: int):
        self.longitude = longitude
        self.latitude = latitude
        self.start_stamp = copy.deepcopy(start_stamp)
        self.last_stamp = copy.deepcopy(last_stamp)
        self.count = count
        self.is_valid = is_valid
        self.first_index = first_index
        self.last_index = last_index
        return


class WatchGPSData:
    def __init__(self):
        self.has_data = False
        self.data_has_changed = False
        self.index = 0
        self.data_size = 0
        self.gps_data = list()
        self.gps_window = 10
        self.window_size_adj_rate = 1
        self.step_delta_rate = 1
        self.lon_min = 0.0
        self.lon_max = 0.0
        self.lat_min = 0.0
        self.lat_max = 0.0
        self.geo_data_frame = None
        self.colors = list()
        self.sizes = list()
        self.fields = None
        return

    def update_config(self, wconfig: VizConfig):
        self.gps_window = wconfig.gps_window_size
        self.window_size_adj_rate = wconfig.gps_win_size_adj_rate
        self.step_delta_rate = wconfig.gps_step_delta_rate

        # Apply critical logic to window sizes.
        self.apply_window_variable_logic()

        # Save any changes back to the config object.
        self.set_config_obj(wconfig=wconfig)

        if self.has_data:
            # Update the data frame.
            self.update_gps_data_frame()
        return

    def apply_window_variable_logic(self):
        if self.has_data:
            if self.data_size < self.gps_window:
                self.gps_window = self.data_size
            if self.data_size < self.window_size_adj_rate:
                self.window_size_adj_rate = int(self.data_size / 2)
            if self.data_size < self.step_delta_rate:
                self.step_delta_rate = int(self.data_size / 2)
        return

    def set_config_obj(self, wconfig: VizConfig):
        wconfig.gps_window_size = self.gps_window
        wconfig.gps_win_size_adj_rate = self.window_size_adj_rate
        wconfig.gps_step_delta_rate = self.step_delta_rate
        return

    def get_first_stamp(self) -> str:
        msg = '...'
        if self.has_data:
            msg = str(self.gps_data[self.gps_window - 1].last_stamp)
        return msg

    def get_current_stamp(self) -> str:
        msg = '...'
        if self.has_data:
            msg = str(self.gps_data[self.index + self.gps_window - 1].last_stamp)
        return msg

    def get_last_stamp(self) -> str:
        msg = '...'
        if self.has_data:
            msg = str(self.gps_data[-1].last_stamp)
        return msg

    def increase_window_size(self) -> bool:
        action = False
        if (self.index + self.gps_window + self.window_size_adj_rate) < self.data_size:
            self.gps_window += self.window_size_adj_rate
            self.update_gps_data_frame()
            action = True
        return action

    def decrease_window_size(self) -> bool:
        action = False
        if (self.gps_window - self.window_size_adj_rate) >= 1:
            self.gps_window -= self.window_size_adj_rate
            self.update_gps_data_frame()
            action = True
        return action

    def step_forward(self) -> bool:
        action = False
        if (self.index + self.gps_window + self.step_delta_rate) < self.data_size:
            self.index += self.step_delta_rate
            self.update_gps_data_frame()
            action = True
        return action

    def step_backward(self) -> bool:
        action = False
        if (self.index - self.step_delta_rate) >= 0:
            self.index -= self.step_delta_rate
            self.update_gps_data_frame()
            action = True
        return action

    def goto_index(self, clicked_float: float):
        if 0.0 <= clicked_float <= 1.0:
            self.index = int(clicked_float * (self.data_size - self.gps_window))
            self.update_gps_data_frame()
        return

    def update_gps_data_frame(self):
        del self.geo_data_frame
        del self.colors
        del self.sizes
        self.colors = list()
        self.sizes = list()
        my_points = dict({'point_id': list(),
                          'Latitude': list(),
                          'Longitude': list()})
        j = 0
        last_stamp = ''
        for i in range(self.index, self.index + self.gps_window):
            my_points['point_id'].append(j)
            my_points['Latitude'].append(self.gps_data[i].latitude)
            my_points['Longitude'].append(self.gps_data[i].longitude)
            if self.gps_data[i].is_valid:
                self.colors.append('g')
            else:
                self.colors.append('r')
            self.sizes.append(20.0)
            last_stamp = str(self.gps_data[i].last_stamp)
            j += 1
        self.sizes[-1] = 80.0

        # print('last stamp:  {}'.format(last_stamp))

        df = pd.DataFrame(my_points)
        df = gpd.GeoDataFrame(df,
                              crs="EPSG:4326",
                              geometry=gpd.points_from_xy(df['Longitude'], df['Latitude']))
        self.geo_data_frame = df.to_crs(epsg=3857)
        # print(self.geo_data_frame.info())
        # print(self.geo_data_frame.head())
        return

    def mark_window_invalid(self):
        for i in range(self.index, self.index + self.gps_window):
            self.gps_data[i].is_valid = False
        self.data_has_changed = True
        self.update_gps_data_frame()
        return

    def mark_window_valid(self):
        for i in range(self.index, self.index + self.gps_window):
            self.gps_data[i].is_valid = True
        self.data_has_changed = True
        self.update_gps_data_frame()
        return

    def plot_gps(self, axis):
        if self.geo_data_frame is not None:
            axis.set_axis_off()
            if self.gps_window > 1:
                self.geo_data_frame['LINE'] = [(LineString([[a.x, a.y], [b.x, b.y]])
                                                if b is not None else None)
                                               for (a, b) in zip(self.geo_data_frame.geometry,
                                                                 self.geo_data_frame.geometry.shift(
                                                                     -1, axis=0))]
                geo_line = gpd.GeoDataFrame(self.geo_data_frame, geometry='LINE')
                geo_line.plot(ax=axis, edgecolor='black', lw=0.2)
            self.geo_data_frame.plot(ax=axis, color=self.colors, markersize=self.sizes)
            minx, miny, maxx, maxy = self.geo_data_frame.total_bounds
            meanx = (minx + maxx) / 2.0
            meany = (miny + maxy) / 2.0
            diffx = (maxx - minx) * 1.1
            diffy = (maxy - miny) * 1.1
            # print('x ', minx, maxx, diffx)
            # print('y ', miny, maxy, diffy)
            if abs(diffx) < 300.0:
                diffx = 300.0
            if abs(diffy) < 300.0:
                diffy = 300.0
            if diffx < diffy:
                diffx = diffy
            else:
                diffy = diffx
            minx = meanx - (diffx / 2.0)
            maxx = meanx + (diffx / 2.0)
            # miny = miny - (0.1 * diffy)
            # maxy = maxy + (0.1 * diffy)
            miny = meany - (diffy / 2.0)
            maxy = meany + (diffy / 2.0)
            # print('nx ', minx, maxx, diffx)
            # print('ny ', miny, maxy, diffy)
            axis.set_xlim(minx, maxx)
            axis.set_ylim(miny, maxy)
            cx.add_basemap(ax=axis, source=cx.providers.OpenStreetMap.Mapnik)
        return

    def load_data_init(self):
        del self.gps_data
        self.gps_data = list()
        self.has_data = False
        self.data_has_changed = False
        self.index = 0
        self.data_size = 0
        self.gps_window = 10
        return

    def load_data_end(self):
        if len(self.gps_data) > 0:
            self.data_size = len(self.gps_data)
            self.has_data = True
            self.data_has_changed = False
            self.apply_window_variable_logic()
            self.update_gps_data_frame()
        else:
            self.load_data_init()
        return
