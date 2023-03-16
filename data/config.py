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

DEFAULT_GPS_VALID = 'g'
DEFAULT_GPS_INVALID = 'b'
DEFAULT_GPS_WINDOW_SIZE = 10
DEFAULT_GPS_STEP_DELTA = 1
DEFAULT_GPS_WIN_SIZE_ADJ = 1
DEFAULT_SEN_WINDOW_SIZE = 500
DEFAULT_SEN_STEP_DELTA = 10
DEFAULT_SEN_WIN_SIZE_ADJ = 10
DEFAULT_REMOVE_ANNOTATION_KEY = 'R'
DEFAULT_LABEL_SEARCH_MINUTES = 60
DEFAULT_NOTES_SEARCH_MINUTES = 60


class VizConfig:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.add_section(section='gps')
        self.config.add_section(section='graphs')
        self.config.add_section(section='annotations')
        self.config.add_section(section='special')
        self.filename = None
        self.gps_valid = DEFAULT_GPS_VALID
        self.gps_invalid = DEFAULT_GPS_INVALID
        self.annotations = dict()
        self.gps_window_size = DEFAULT_GPS_WINDOW_SIZE
        self.gps_step_delta_rate = DEFAULT_GPS_STEP_DELTA
        self.gps_win_size_adj_rate = DEFAULT_GPS_WIN_SIZE_ADJ
        self.sensors_window_size = DEFAULT_SEN_WINDOW_SIZE
        self.sensors_step_delta_rate = DEFAULT_SEN_STEP_DELTA
        self.sensors_win_size_adj_rate = DEFAULT_SEN_WIN_SIZE_ADJ
        self.remove_annotation_key = DEFAULT_REMOVE_ANNOTATION_KEY
        self.label_search_minutes = DEFAULT_LABEL_SEARCH_MINUTES
        self.notes_search_minutes = DEFAULT_NOTES_SEARCH_MINUTES
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
        # Load the labeling values.
        self.gps_valid = self.config.get(section='gps',
                                         option='valid',
                                         fallback=DEFAULT_GPS_VALID)
        self.gps_invalid = self.config.get(section='gps',
                                           option='invalid',
                                           fallback=DEFAULT_GPS_INVALID)
        if 'annotations' in self.config.sections():
            for key in list(self.config['annotations'].keys()):
                self.annotations[key] = self.config['annotations'][key]
        if 'special' in self.config.sections():
            self.remove_annotation_key = self.config.get(section='special',
                                                         option='key_to_remove_annotations',
                                                         fallback=DEFAULT_REMOVE_ANNOTATION_KEY)
            if self.remove_annotation_key in self.annotations:
                raise ValueError('\nERROR:  The key_to_remove_annotations value is the same as '
                                 'one of the annotation keys!  This must be a different key than '
                                 'one of the annotation keys, please change it to a different '
                                 'value in config.conf and try again.\n')
        # Load the window configs.
        self.gps_window_size = self.config.getint(section='graphs',
                                                  option='gps_window_size',
                                                  fallback=DEFAULT_GPS_WINDOW_SIZE)
        self.gps_step_delta_rate = self.config.getint(section='graphs',
                                                      option='gps_step_delta_rate',
                                                      fallback=DEFAULT_GPS_STEP_DELTA)
        self.gps_win_size_adj_rate = self.config.getint(section='graphs',
                                                        option='gps_win_size_adj_rate',
                                                        fallback=DEFAULT_GPS_WIN_SIZE_ADJ)
        self.sensors_window_size = self.config.getint(section='graphs',
                                                      option='sensors_window_size',
                                                      fallback=DEFAULT_SEN_WINDOW_SIZE)
        self.sensors_step_delta_rate = self.config.getint(section='graphs',
                                                          option='sensors_step_delta_rate',
                                                          fallback=DEFAULT_SEN_STEP_DELTA)
        self.sensors_win_size_adj_rate = self.config.getint(section='graphs',
                                                            option='sensors_win_size_adj_rate',
                                                            fallback=DEFAULT_SEN_WIN_SIZE_ADJ)
        self.label_search_minutes = self.config.getint(section='graphs',
                                                       option='label_search_minutes',
                                                       fallback=DEFAULT_LABEL_SEARCH_MINUTES)
        self.notes_search_minutes = self.config.getint(section='graphs',
                                                       option='notes_search_minutes',
                                                       fallback=DEFAULT_NOTES_SEARCH_MINUTES)
        return

    def save_config(self, filename: str = None):
        # Set the graph config values.
        self.config.set(section='graphs',
                        option='gps_window_size',
                        value=str(self.gps_window_size))
        self.config.set(section='graphs',
                        option='gps_step_delta_rate',
                        value=str(self.gps_step_delta_rate))
        self.config.set(section='graphs',
                        option='gps_win_size_adj_rate',
                        value=str(self.gps_win_size_adj_rate))
        self.config.set(section='graphs',
                        option='sensors_window_size',
                        value=str(self.sensors_window_size))
        self.config.set(section='graphs',
                        option='sensors_step_delta_rate',
                        value=str(self.sensors_step_delta_rate))
        self.config.set(section='graphs',
                        option='sensors_win_size_adj_rate',
                        value=str(self.sensors_win_size_adj_rate))
        self.config.set(section='graphs',
                        option='label_search_minutes',
                        value=str(self.label_search_minutes))
        self.config.set(section='graphs',
                        option='notes_search_minutes',
                        value=str(self.notes_search_minutes))
        # Set the labeling values.
        self.config.set(section='gps', option='valid', value=self.gps_valid)
        self.config.set(section='gps', option='invalid', value=self.gps_invalid)
        for key in list(self.annotations.keys()):
            self.config.set(section='annotations', option=key, value=self.annotations[key])
        if filename is not None:
            self.filename = filename
        configfile = open(self.filename, 'w')
        self.config.write(configfile)
        configfile.close()
        return

