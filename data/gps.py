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
import matplotlib.pyplot as plt
plt.style.use('ggplot')
plt.rcParams.update({'font.size': 16,
                     'axes.labelweight': 'bold',
                     'figure.figsize': (6, 6),
                     'axes.edgecolor': '0.2'})


class GPSData:
    def __init__(self, longitude: float, latitude: float, start_stamp: datetime.datetime,
                 last_stamp: datetime.datetime, count: int, is_valid: bool):
        self.longitude = longitude
        self.latitude = latitude
        self.start_stamp = copy.deepcopy(start_stamp)
        self.last_stamp = copy.deepcopy(last_stamp)
        self.count = count
        self.is_valid = is_valid
        return


# gps_data = list()
# with MobileData('/media/zfs/data/local/work/mink/data/sttr008.test', 'r') as mdata:
#     cur_lat = -1.0
#     cur_lon = -1.0
#     first_stamp = None
#     mlast_stamp = None
#     mcount = 0
#     for row in mdata.rows_dict:
#         if row['latitude'] is None or row['longitude'] is None:
#             continue
#         if row['latitude'] != cur_lat or row['longitude'] != cur_lon:
#             if len(gps_data) > 0:
#                 print(gps_data[-1].count, gps_data[-1].longitude, gps_data[-1].latitude)
#             mcount = 1
#             first_stamp = copy.deepcopy(row['stamp'])
#             mlast_stamp = copy.deepcopy(row['stamp'])
#             cur_lat = row['latitude']
#             cur_lon = row['longitude']
#             gps_data.append(GPSData(longitude=cur_lon,
#                                     latitude=cur_lat,
#                                     start_stamp=first_stamp,
#                                     last_stamp=mlast_stamp,
#                                     count=mcount,
#                                     is_valid=True))
#         else:
#             gps_data[-1].count += 1
#             gps_data[-1].last_stamp = copy.deepcopy(row['stamp'])
#
# lon_min = gps_data[0].longitude
# lon_max = gps_data[0].longitude
# lat_min = gps_data[0].latitude
# lat_max = gps_data[0].latitude
# print('size of gps_data: {}'.format(len(gps_data)))
# my_points = dict({'point_id': list(),
#                   'Latitude': list(),
#                   'Longitude': list()})
#
#
# for i in range(len(gps_data)):
#     my_points['point_id'].append(i)
#     my_points['Latitude'].append(gps_data[i].latitude)
#     my_points['Longitude'].append(gps_data[i].longitude)
#     if gps_data[i].longitude < lon_min:
#         lon_min = gps_data[i].longitude
#     if gps_data[i].longitude > lon_max:
#         lon_max = gps_data[i].longitude
#     if gps_data[i].latitude < lat_min:
#         lat_min = gps_data[i].latitude
#     if gps_data[i].latitude > lat_max:
#         lat_max = gps_data[i].latitude
#
# d = pd.DataFrame(my_points)
# d = gpd.GeoDataFrame(d,
#                      crs="EPSG:4326",
#                      geometry=gpd.points_from_xy(d['Longitude'], d['Latitude']))
# df = d.to_crs(epsg=3857)
#
# ax = df.plot(edgecolor="0.2")
# cx.add_basemap(ax)
#
# print('latitude min: {}'.format(lat_min))
# print('latitude max: {}'.format(lat_max))
# print('longitude min: {}'.format(lon_min))
# print('longitude max: {}'.format(lon_max))
#
# # G = ox.graph_from_bbox(lat_max, lat_min, lon_max, lon_min, network_type='all')
# # area = (ox.graph_to_gdfs(G, nodes=False)
# #         .reset_index(drop=True)
# #         .loc[:, ['name', 'length', 'bridge', 'geometry']])
# # area.plot(edgecolor='0.2')
# plt.title('sttr001.test')
# plt.show()
