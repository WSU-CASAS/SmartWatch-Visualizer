from .mobile_al_data import MobileData
import copy
import datetime
import os
import numpy as np
import osmnx as ox
import pandas as pd
import geopandas as gpd
import contextily as cx
from shapely.geometry import Point
from .gps import GPSData
import matplotlib.pyplot as plt
plt.style.use('ggplot')
plt.rcParams.update({'font.size': 16,
                     'axes.labelweight': 'bold',
                     'figure.figsize': (6, 6),
                     'axes.edgecolor': '0.2'})


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
        return

    def increase_window_size(self) -> bool:
        action =  False
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
        my_points = dict({'point_id': list(),
                          'Latitude': list(),
                          'Longitude': list()})
        j = 0
        for i in range(self.index, self.index + self.gps_window):
            my_points['point_id'].append(j)
            my_points['Latitude'].append(self.gps_data[i].latitude)
            my_points['Longitude'].append(self.gps_data[i].longitude)
            j += 1

        df = pd.DataFrame(my_points)
        df = gpd.GeoDataFrame(df,
                              crs="EPSG:4326",
                              geometry=gpd.points_from_xy(df['Longitude'], df['Latitude']))
        self.geo_data_frame = df.to_crs(epsg=3857)
        return

    def plot_gps(self, axis):
        if self.geo_data_frame is not None:
            self.geo_data_frame.plot(ax=axis, edgecolor='0.2')
            cx.add_basemap(ax=axis)
        return

    def load_data(self, filename: str, update_callback=None, done_callback=None):
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
                        msg = '{}  {}  {}  {}'.format(self.gps_data[-1].count,
                                                      str(self.gps_data[-1].last_stamp),
                                                      self.gps_data[-1].longitude,
                                                      self.gps_data[-1].latitude)
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

        if done_callback is not None:
            done_callback()
        return

