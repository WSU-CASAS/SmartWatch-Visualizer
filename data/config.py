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
# **  permission from Washington State # University
# **
# ** Contact: Brian L. Thomas (bthomas1@wsu.edu)
# *****************************************************************************#
import configparser
import os


class VizConfig:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.filename = None
        self.gps_valid = 'g'
        self.gps_invalid = 'b'
        self.annotations = dict()
        return

    def set(self, group: str, item: str, value: str):
        self.config.set(group, item, value)
        return

    def get(self, group: str, item: str, default: str = None) -> str:
        value = default
        if self.config.has_option(group, item):
            value = self.config.get(group, item)
        return value

    def load_config(self, filename: str):
        if filename is not None:
            if os.path.isfile(filename):
                self.filename = filename
                self.config.read(self.filename)
        self.gps_valid = self.get(group='gps', item='valid', default=self.gps_valid)
        self.gps_invalid = self.get(group='gps', item='invalid', default=self.gps_invalid)
        if 'annotations' in self.config.sections():
            for key in list(self.config['annotations'].keys()):
                self.annotations[key] = self.config['annotations'][key]
        return

    def save_config(self, filename: str = None):
        if filename is not None:
            self.filename = filename
        configfile = open(self.filename, 'w')
        self.config.write(configfile)
        configfile.close()
        return

