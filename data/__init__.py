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
import copy
import datetime
import os
import numpy as np
import pandas as pd
import geopandas as gpd
import contextily as cx
from shapely.geometry import Point, LineString
from .gps import GPSData
import matplotlib.pyplot as plt

plt.style.use('ggplot')
plt.rcParams.update({'font.size': 16,
                     'axes.labelweight': 'bold',
                     'figure.figsize': (6, 6),
                     'axes.edgecolor': '0.2'})
cx.set_cache_dir(path='data/contextily_cache')


class WatchData:
    def __init__(self):
        self.has_data = False
        self.index = 0
        self.data_size = 0
        self.gps_data = list()
        self.gps_window = 10
        self.lon_min = 0.0
        self.lon_max = 0.0
        self.lat_min = 0.0
        self.lat_max = 0.0
        self.geo_data_frame = None
        self.colors = list()
        self.sizes = list()
        return

    def increase_window_size(self) -> bool:
        action = False
        if (self.index + self.gps_window + 1) < self.data_size:
            self.gps_window += 1
            self.update_gps_data_frame()
            action = True
        return action

    def decrease_window_size(self) -> bool:
        action = False
        if (self.gps_window - 1) >= 1:
            self.gps_window -= 1
            self.update_gps_data_frame()
            action = True
        return action

    def step_forward(self) -> bool:
        action = False
        if (self.index + self.gps_window + 1) < self.data_size:
            self.index += 1
            self.update_gps_data_frame()
            action = True
        return action

    def step_backward(self) -> bool:
        action = False
        if (self.index - 1) >= 0:
            self.index -= 1
            self.update_gps_data_frame()
            action = True
        return action

    def goto_index(self, clicked_float: float):
        if 0.0 <= clicked_float <= 1.0:
            self.index = int(clicked_float * self.data_size)
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
        for i in range(self.index, self.index + self.gps_window):
            my_points['point_id'].append(j)
            my_points['Latitude'].append(self.gps_data[i].latitude)
            my_points['Longitude'].append(self.gps_data[i].longitude)
            if self.gps_data[i].is_valid:
                self.colors.append('g')
            else:
                self.colors.append('r')
            self.sizes.append(20.0)
            j += 1
        self.sizes[-1] = 50.0

        df = pd.DataFrame(my_points)
        df = gpd.GeoDataFrame(df,
                              crs="EPSG:4326",
                              geometry=gpd.points_from_xy(df['Longitude'], df['Latitude']))
        self.geo_data_frame = df.to_crs(epsg=3857)
        print(self.geo_data_frame.info())
        print(self.geo_data_frame.head())
        return

    def mark_window_invalid(self):
        for i in range(self.index, self.index + self.gps_window):
            self.gps_data[i].is_valid = False
        self.update_gps_data_frame()
        return

    def mark_window_valid(self):
        for i in range(self.index, self.index + self.gps_window):
            self.gps_data[i].is_valid = True
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
            print('x ', minx, maxx, diffx)
            print('y ', miny, maxy, diffy)
            if abs(diffx) < 400.0:
                diffx = 400.0
            if abs(diffy) < 400.0:
                diffy = 400.0
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
            print('nx ', minx, maxx, diffx)
            print('ny ', miny, maxy, diffy)
            axis.set_xlim(minx, maxx)
            axis.set_ylim(miny, maxy)
            cx.add_basemap(ax=axis, source=cx.providers.OpenStreetMap.Mapnik)
        return

    def load_data(self, filename: str, update_callback=None, done_callback=None):
        del self.gps_data
        self.gps_data = list()
        self.has_data = False
        self.index = 0
        self.data_size = 0
        self.gps_window = 10
        with MobileData(filename, 'r') as mdata:
            cur_lat = -1.0
            cur_lon = -1.0
            first_stamp = None
            mlast_stamp = None
            mcount = 0
            for row in mdata.rows_dict:
                if row['latitude'] is None or row['longitude'] is None:
                    continue
                if row['latitude'] != cur_lat or row['longitude'] != cur_lon:
                    if len(self.gps_data) > 0:
                        msg = '{}  {}'.format(self.gps_data[-1].count,
                                              str(self.gps_data[-1].last_stamp))
                        print(msg)
                        if update_callback is not None:
                            update_callback(msg)
                    mcount = 1
                    first_stamp = copy.deepcopy(row['stamp'])
                    mlast_stamp = copy.deepcopy(row['stamp'])
                    cur_lat = row['latitude']
                    cur_lon = row['longitude']
                    self.gps_data.append(GPSData(longitude=cur_lon,
                                                 latitude=cur_lat,
                                                 start_stamp=first_stamp,
                                                 last_stamp=mlast_stamp,
                                                 count=mcount,
                                                 is_valid=True))
                else:
                    self.gps_data[-1].count += 1
                    self.gps_data[-1].last_stamp = copy.deepcopy(row['stamp'])

        if len(self.gps_data) > 0:
            self.data_size = len(self.gps_data)
            self.has_data = True
            self.update_gps_data_frame()

        if done_callback is not None:
            done_callback()
        return
