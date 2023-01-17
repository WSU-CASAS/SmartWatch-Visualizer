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


class SingleDataWindow:
    def __init__(self, i_start: int, i_last: int, label: str):
        self.i_start = i_start
        self.i_last = i_last
        self.label = label
        return


class DataWindowList:
    def __init__(self):
        self.list = list()
        self.index = 0
        return

    def add_window(self, window: SingleDataWindow):
        self.list.append(copy.deepcopy(window))
        return
