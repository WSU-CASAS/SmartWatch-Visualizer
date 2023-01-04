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

