#!/usr/bin/env python3
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

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Gio, GObject
import datetime
import random
import threading
from matplotlib.backends.backend_gtk3agg import FigureCanvas  # or gtk3cairo.
from matplotlib.figure import Figure
import matplotlib.style as mplstyle
from data import WatchData
from data.config import VizConfig
from data import MODE_GPS, MODE_SENSORS
from data.annotate import DataWindowList, SingleDataWindow

mplstyle.use(['fast'])

MODE_FIRST_WINDOW = 0
MODE_OPENING_FILE = 1
MODE_GPS_VISUALIZATION = 2
MODE_SAVING_FILE = 3
MODE_SENSOR_VISUALIZATION = 4
MODE_ANNOTATION_HELP = 5


class SmartWatchVisualizer:
    @staticmethod
    def build_spinbutton_listboxrow(button: Gtk.SpinButton, label: str, value: int) \
            -> Gtk.ListBoxRow:
        row = Gtk.ListBoxRow()
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        row.add(hbox)
        item_label = Gtk.Label(label=label)
        hbox.pack_start(item_label, True, True, 0)
        button.set_value(value=value)
        hbox.pack_start(button, False, True, 0)
        return row

    def on_edit_settings_clicked(self, widget):
        self.settings = Gtk.Window(transient_for=self.window,
                                   destroy_with_parent=True,
                                   title='Edit Settings')
        self.settings.set_border_width(10)
        # Main box of the window.
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.settings.add(main_box)
        # Label for the graph section.
        graph_label = Gtk.Label(label='Visualization Navigation Settings')
        graph_label.set_justify(Gtk.Justification.LEFT)
        main_box.pack_start(graph_label, True, True, 0)
        # Contents of the graph section.
        listbox = Gtk.ListBox()
        listbox.set_selection_mode(mode=Gtk.SelectionMode.NONE)
        main_box.pack_start(listbox, True, True, 0)

        self.sb_gps_window_size = Gtk.SpinButton()
        self.set_spinbutton_defaults(button=self.sb_gps_window_size,
                                     value=self.config.gps_window_size)
        self.sb_gps_step_delta_rate = Gtk.SpinButton()
        self.set_spinbutton_defaults(button=self.sb_gps_step_delta_rate,
                                     value=self.config.gps_step_delta_rate)
        self.sb_gps_win_size_adj_rate = Gtk.SpinButton()
        self.set_spinbutton_defaults(button=self.sb_gps_win_size_adj_rate,
                                     value=self.config.gps_win_size_adj_rate)
        self.sb_sen_window_size = Gtk.SpinButton()
        self.set_spinbutton_defaults(button=self.sb_sen_window_size,
                                     value=self.config.sensors_window_size)
        self.sb_sen_step_delta_rate = Gtk.SpinButton()
        self.set_spinbutton_defaults(button=self.sb_sen_step_delta_rate,
                                     value=self.config.sensors_step_delta_rate)
        self.sb_sen_win_size_adj_rate = Gtk.SpinButton()
        self.set_spinbutton_defaults(button=self.sb_sen_win_size_adj_rate,
                                     value=self.config.sensors_win_size_adj_rate)

        # Graph spinbutton entries.
        row = self.build_spinbutton_listboxrow(button=self.sb_gps_window_size,
                                               label='GPS Window Size',
                                               value=self.config.gps_window_size)
        listbox.add(row)
        row = self.build_spinbutton_listboxrow(button=self.sb_gps_win_size_adj_rate,
                                               label='GPS Window Size Change Steps',
                                               value=self.config.gps_win_size_adj_rate)
        listbox.add(row)
        row = self.build_spinbutton_listboxrow(button=self.sb_gps_step_delta_rate,
                                               label='GPS Left/Right Step Size',
                                               value=self.config.gps_step_delta_rate)
        listbox.add(row)
        row = self.build_spinbutton_listboxrow(button=self.sb_sen_window_size,
                                               label='Sensors Window Size',
                                               value=self.config.sensors_window_size)
        listbox.add(row)
        row = self.build_spinbutton_listboxrow(button=self.sb_sen_win_size_adj_rate,
                                               label='Sensors Window Size Change Steps',
                                               value=self.config.sensors_win_size_adj_rate)
        listbox.add(row)
        row = self.build_spinbutton_listboxrow(button=self.sb_sen_step_delta_rate,
                                               label='Sensors Left/Right Step Size',
                                               value=self.config.sensors_step_delta_rate)
        listbox.add(row)

        # Ok/Cancel buttons at the bottom.
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=100)
        main_box.pack_start(hbox, True, True, 0)
        btn_ok = Gtk.Button(label='OK')
        btn_cancel = Gtk.Button(label='Cancel')
        hbox.pack_start(btn_ok, False, True, 0)
        hbox.pack_start(btn_cancel, False, True, 0)

        btn_ok.connect('clicked', self.cb_settings_buttons, 'Ok')
        btn_cancel.connect('clicked', self.cb_settings_buttons, 'Cancel')

        self.settings.show_all()
        return

    def cb_settings_buttons(self, button, value):
        if value == 'Cancel':
            self.settings.hide()
            self.settings = None
        elif value == 'Ok':
            self.settings.hide()
            self.config.gps_window_size = self.sb_gps_window_size.get_value_as_int()
            self.config.gps_win_size_adj_rate = self.sb_gps_win_size_adj_rate.get_value_as_int()
            self.config.gps_step_delta_rate = self.sb_gps_step_delta_rate.get_value_as_int()
            self.config.sensors_window_size = self.sb_sen_window_size.get_value_as_int()
            self.config.sensors_win_size_adj_rate = self.sb_sen_win_size_adj_rate.get_value_as_int()
            self.config.sensors_step_delta_rate = self.sb_sen_step_delta_rate.get_value_as_int()
            self.data.update_config(wconfig=self.config)
            if self.data.has_data():
                GLib.idle_add(self.draw_canvas)
        return

    def on_file_save_as_clicked(self, widget):
        ffilter = Gtk.FileFilter()
        ffilter.add_pattern('*.data')
        ffilter.add_pattern('*.csv')
        ffilter.set_name('Data Files')
        filterall = Gtk.FileFilter()
        filterall.add_pattern('*')
        filterall.set_name('All Files')
        get_file = Gtk.FileChooserDialog(title='Please select a data file',
                                         parent=self.window,
                                         action=Gtk.FileChooserAction.SAVE)
        get_file.add_buttons(Gtk.STOCK_CANCEL,
                             Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_SAVE_AS,
                             Gtk.ResponseType.OK)
        get_file.add_filter(filter=ffilter)
        get_file.add_filter(filter=filterall)

        response = get_file.run()
        if response == Gtk.ResponseType.OK:
            file_path = get_file.get_filename()
            self.opened_filename = file_path
            print('Saving to file: {}'.format(self.opened_filename))
            thread = threading.Thread(target=self.threaded_save_data, args=(self.opened_filename,))
            thread.daemon = True

            self.set_status_message(message='Saving file...  This may take some time.')
            self.STATE = MODE_SAVING_FILE
            self.update_visible_state()

            thread.start()

        get_file.destroy()
        return

    def on_file_save_clicked(self, widget):
        print('Saving to file: {}'.format(self.opened_filename))
        thread = threading.Thread(target=self.threaded_save_data, args=(self.opened_filename,))
        thread.daemon = True

        self.set_status_message(message='Saving file...  This may take some time.')
        self.STATE = MODE_SAVING_FILE
        self.update_visible_state()

        thread.start()
        return

    def threaded_save_data(self, filename):
        self.data.save_data(filename=filename,
                            update_callback=self.threaded_callback_update_loading_label,
                            done_callback=self.callback_saving_file_done)
        return

    def callback_saving_file_done(self):
        self.STATE = MODE_GPS_VISUALIZATION
        self.data_modified = False
        GLib.idle_add(self.set_clean_title)
        GLib.idle_add(self.set_status_message, 'Ready')
        GLib.idle_add(self.update_visible_state)
        GLib.idle_add(self.draw_canvas)
        return

    def on_file_open_clicked(self, widget):
        ffilter = Gtk.FileFilter()
        ffilter.add_pattern('*.data')
        ffilter.add_pattern('*.csv')
        ffilter.set_name('Data Files')
        filterall = Gtk.FileFilter()
        filterall.add_pattern('*')
        filterall.set_name('All Files')
        get_file = Gtk.FileChooserDialog(title='Please select a data file',
                                         parent=self.window,
                                         action=Gtk.FileChooserAction.OPEN)
        get_file.add_buttons(Gtk.STOCK_CANCEL,
                             Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_OPEN,
                             Gtk.ResponseType.OK)
        get_file.add_filter(filter=ffilter)
        get_file.add_filter(filter=filterall)

        response = get_file.run()
        if response == Gtk.ResponseType.OK:
            file_path = get_file.get_filename()
            print('file selected!  {}'.format(file_path))
            thread = threading.Thread(target=self.threaded_load_data, args=(file_path,))
            thread.daemon = True

            self.set_status_message(message='Loading file...  This may take some time.')
            self.STATE = MODE_OPENING_FILE
            self.update_visible_state()
            self.opened_filename = file_path

            thread.start()

        get_file.destroy()
        return

    def threaded_load_data(self, filename):
        self.data.load_data(filename=filename,
                            update_callback=self.threaded_callback_update_loading_label,
                            done_callback=self.callback_loading_file_done)
        return

    def threaded_callback_update_loading_label(self, text):
        GLib.idle_add(self.threaded_update_loading_file_label, text)
        return

    def threaded_update_loading_file_label(self, text):
        self.lbl_loading_file.set_text(text)
        return

    def callback_loading_file_done(self):
        self.data_modified = False
        GLib.idle_add(self.set_clean_title)
        if self.data.has_data():
            if self.data.has_gps_data():
                self.STATE = MODE_GPS_VISUALIZATION
                self.data.set_mode(mode=MODE_GPS)
                self.mode_gps_item.set_active(True)
            else:
                self.STATE = MODE_SENSOR_VISUALIZATION
                self.data.set_mode(mode=MODE_SENSORS)
                self.mode_sensor_item.set_active(True)
            self.data.update_config(wconfig=self.config)
            GLib.idle_add(self.set_status_message, 'Ready')
            GLib.idle_add(self.set_all_lbl_progress)
            GLib.idle_add(self.update_visible_state)
            GLib.idle_add(self.draw_canvas)
        else:
            self.STATE = MODE_FIRST_WINDOW
            GLib.idle_add(self.set_status_message, 'There is no data to visualize.')
            GLib.idle_add(self.update_visible_state)
        return

    def set_all_lbl_progress(self):
        self.lbl_progress_start.set_text(self.data.get_first_stamp())
        self.lbl_progress_current.set_text(self.data.get_current_stamp())
        self.lbl_progress_end.set_text(self.data.get_last_stamp())
        return

    def set_first_current_lbl_progress(self):
        self.lbl_progress_start.set_text(self.data.get_first_stamp())
        self.lbl_progress_current.set_text(self.data.get_current_stamp())
        return

    def set_current_lbl_progress(self):
        self.lbl_progress_current.set_text(self.data.get_current_stamp())
        return

    def set_status_message(self, message: str, context_id: int = 0):
        self.status_bar.push(context_id, message)
        return

    def pop_status_message(self, context_id: int = 0):
        self.status_bar.pop(context_id)
        return

    def draw_canvas(self):
        self.set_status_message(message='Loading image...', context_id=1)
        # Allow redraw for loading image text when running GPS visualization.
        if self.STATE in [MODE_GPS_VISUALIZATION, MODE_ANNOTATION_HELP]:
            GLib.idle_add(self.draw_canvas_next)
        else:
            self.draw_canvas_next()
        return

    def draw_canvas_next(self):
        if self.STATE == MODE_ANNOTATION_HELP:
            i = self.data_windows.list[self.data_windows.index].i_start
            self.progress.set_fraction(float(i)/float(self.data.data_size()))
            self.ax.cla()
            self.axes1.cla()
            self.axes2.cla()
            self.axes3.cla()
            self.data.plot_given_window(data_window=self.data_windows.list[self.data_windows.index],
                                        axis1=self.axes1,
                                        axis2=self.axes2,
                                        axis3=self.axes3,
                                        axis=self.ax)
            self.ax.set_axis_off()
            self.canvas.draw_idle()
            self.canvas.flush_events()
            self.canvas2.draw_idle()
            self.canvas2.flush_events()
            self.lbl_labels.set_text(self.data.get_given_label_text(
                data_window=self.data_windows.list[self.data_windows.index]))
        else:
            if self.data.has_data():
                self.progress.set_fraction(float(self.data.index())/float(self.data.data_size()))
            if self.mode_gps_item.get_active():
                self.ax.cla()
                self.data.plot_gps(self.ax)
                self.ax.set_axis_off()
                # self.canvas.draw()
                self.canvas.draw_idle()
                self.canvas.flush_events()
            else:
                # print('draw for sensors')
                self.axes1.cla()
                self.axes2.cla()
                self.axes3.cla()
                self.data.plot_sensors(axis1=self.axes1,
                                       axis2=self.axes2,
                                       axis3=self.axes3)
                self.canvas2.draw_idle()
                self.canvas2.flush_events()
                self.lbl_labels.set_text(self.data.get_label_text())
        self.pop_status_message(context_id=1)
        return

    def timer_tick(self):
        response = True
        if self.STATE != MODE_SENSOR_VISUALIZATION:
            response = False
            self.timer = None
        if self.need_redraw:
            self.draw_canvas_next()
            self.need_redraw = False
        return response

    def on_button_pressed_progress(self, widget, event):
        if self.data.has_data():
            rec = self.eventbox.get_allocated_width()
            f = float(event.x) / float(rec)
            self.data.goto_index(clicked_float=f)
            self.lbl_progress_current.set_text(self.data.get_current_stamp())
            self.draw_canvas()
        return

    def on_key_press_event(self, widget, event):
        # print('key press:  {}'.format(event.string))
        if event.keyval == 65361:       # Left
            # print('LEFT')
            if self.STATE == MODE_ANNOTATION_HELP:
                if (self.data_windows.index - 1) >= 0:
                    self.data_windows.index -= 1
                    GLib.idle_add(self.set_current_lbl_progress)
                    GLib.idle_add(self.draw_canvas)
            elif self.data.step_backward():
                GLib.idle_add(self.set_current_lbl_progress)
                if self.STATE == MODE_SENSOR_VISUALIZATION:
                    self.need_redraw = True
                else:
                    GLib.idle_add(self.draw_canvas)
        elif event.keyval == 65363:     # Right
            # print('RIGHT')
            if self.STATE == MODE_ANNOTATION_HELP:
                if (self.data_windows.index + 1) < len(self.data_windows.list):
                    self.data_windows.index += 1
                    GLib.idle_add(self.set_current_lbl_progress)
                    GLib.idle_add(self.draw_canvas)
            elif self.data.step_forward():
                GLib.idle_add(self.set_current_lbl_progress)
                if self.STATE == MODE_SENSOR_VISUALIZATION:
                    self.need_redraw = True
                else:
                    GLib.idle_add(self.draw_canvas)
        elif event.keyval == 65362:     # Up
            # print('UP')
            if self.data.increase_window_size():
                self.data.set_config_obj(wconfig=self.config)
                GLib.idle_add(self.set_first_current_lbl_progress)
                if self.STATE == MODE_SENSOR_VISUALIZATION:
                    self.need_redraw = True
                else:
                    GLib.idle_add(self.draw_canvas)
        elif event.keyval == 65364:     # Down
            # print('DOWN')
            if self.data.decrease_window_size():
                self.data.set_config_obj(wconfig=self.config)
                GLib.idle_add(self.set_first_current_lbl_progress)
                if self.STATE == MODE_SENSOR_VISUALIZATION:
                    self.need_redraw = True
                else:
                    GLib.idle_add(self.draw_canvas)
        elif self.STATE == MODE_GPS_VISUALIZATION:
            if event.string == self.config.gps_invalid:
                # print(self.config.gps_invalid)
                self.data.mark_window_invalid()
                GLib.idle_add(self.draw_canvas)
                if not self.data_modified:
                    self.data_modified = True
                    GLib.idle_add(self.set_modified_title)
            elif event.string == self.config.gps_valid:
                # print(self.config.gps_valid)
                self.data.mark_window_valid()
                GLib.idle_add(self.draw_canvas)
                if not self.data_modified:
                    self.data_modified = True
                    GLib.idle_add(self.set_modified_title)
        elif self.STATE == MODE_SENSOR_VISUALIZATION:
            if event.string in self.config.annotations.keys():
                self.data.annotate_window(annotation=self.config.annotations[event.string])
                if not self.data_modified:
                    self.data_modified = True
                    GLib.idle_add(self.set_modified_title)
        return True

    def update_visible_state(self):
        if self.STATE == MODE_FIRST_WINDOW:
            self.hbox1.hide()
            self.eventbox.hide()
            self.spinner.stop()
            self.spinner.show()
            self.lbl_loading_file.hide()
            self.canvas.hide()
            self.canvas2.hide()
            self.open_file_item.set_sensitive(True)
            self.save_item.set_sensitive(False)
            self.save_as_item.set_sensitive(False)
            self.mode_gps_item.set_sensitive(False)
            self.mode_sensor_item.set_sensitive(False)
            self.mode_annotation_item.set_sensitive(False)
        elif self.STATE == MODE_OPENING_FILE:
            self.hbox1.hide()
            self.eventbox.hide()
            self.spinner.start()
            self.spinner.show()
            self.lbl_loading_file.show()
            self.canvas.hide()
            self.canvas2.hide()
            self.open_file_item.set_sensitive(False)
            self.save_item.set_sensitive(False)
            self.save_as_item.set_sensitive(False)
            self.mode_gps_item.set_sensitive(False)
            self.mode_sensor_item.set_sensitive(False)
            self.mode_annotation_item.set_sensitive(False)
        elif self.STATE == MODE_GPS_VISUALIZATION:
            self.hbox1.show()
            self.eventbox.show()
            self.spinner.stop()
            self.spinner.hide()
            self.lbl_loading_file.hide()
            self.canvas.show()
            self.canvas2.hide()
            self.open_file_item.set_sensitive(True)
            self.save_item.set_sensitive(True)
            self.save_as_item.set_sensitive(True)
            self.mode_gps_item.set_sensitive(True)
            self.mode_sensor_item.set_sensitive(True)
            self.mode_annotation_item.set_sensitive(True)
        elif self.STATE == MODE_SENSOR_VISUALIZATION:
            self.hbox1.show()
            self.eventbox.show()
            self.spinner.stop()
            self.spinner.hide()
            self.lbl_loading_file.hide()
            self.canvas.hide()
            self.canvas2.show()
            self.open_file_item.set_sensitive(True)
            self.save_item.set_sensitive(True)
            self.save_as_item.set_sensitive(True)
            self.mode_gps_item.set_sensitive(True)
            self.mode_sensor_item.set_sensitive(True)
            self.mode_annotation_item.set_sensitive(True)
        elif self.STATE == MODE_ANNOTATION_HELP:
            self.hbox1.show()
            self.eventbox.show()
            self.spinner.stop()
            self.spinner.hide()
            self.lbl_loading_file.hide()
            self.canvas.show()
            self.canvas2.show()
            self.open_file_item.set_sensitive(True)
            self.save_item.set_sensitive(True)
            self.save_as_item.set_sensitive(True)
            self.mode_gps_item.set_sensitive(True)
            self.mode_sensor_item.set_sensitive(True)
            self.mode_annotation_item.set_sensitive(True)
        elif self.STATE == MODE_SAVING_FILE:
            self.hbox1.hide()
            self.eventbox.hide()
            self.spinner.start()
            self.spinner.show()
            self.lbl_loading_file.show()
            self.canvas.hide()
            self.canvas2.hide()
            self.open_file_item.set_sensitive(False)
            self.save_item.set_sensitive(False)
            self.save_as_item.set_sensitive(False)
            self.mode_gps_item.set_sensitive(False)
            self.mode_sensor_item.set_sensitive(False)
            self.mode_annotation_item.set_sensitive(False)
        return

    def on_mode_toggled(self, widget, mode):
        if widget.get_active():
            if mode == MODE_GPS_VISUALIZATION:
                if self.data.has_gps_data():
                    # Go ahead and set to GPS mode.
                    self.STATE = mode
                    self.data.set_mode(mode=MODE_GPS)
                    self.need_redraw = True
                    self.update_visible_state()
                    if self.labels_win is not None:
                        self.labels_win.hide()
            elif mode == MODE_SENSOR_VISUALIZATION:
                if self.data.has_sensors_data():
                    # Go ahead and set to sensors mode.
                    self.STATE = mode
                    self.data.set_mode(mode=MODE_SENSORS)
                    self.timer = GLib.timeout_add(100, self.timer_tick)
                    self.need_redraw = True
            elif mode == MODE_ANNOTATION_HELP:
                if self.data.has_sensors_data():
                    # Go ahead and set to sensors mode.
                    self.STATE = mode
                    self.data.set_mode(mode=MODE_SENSORS)
                    # self.timer = GLib.timeout_add(100, self.timer_tick)
                    self.need_redraw = True
                    self.build_data_windows()
            if mode in [MODE_SENSOR_VISUALIZATION, MODE_ANNOTATION_HELP]:
                if self.labels_win is None:
                    self.labels_win = Gtk.Window(destroy_with_parent=True,
                                                 title='Labels')
                    self.labels_win.add(self.scrolled_win)
                    self.labels_win.show_all()
                else:
                    self.labels_win.show_all()
            self.update_visible_state()
            GLib.idle_add(self.set_all_lbl_progress)
            GLib.idle_add(self.draw_canvas)
        return

    def build_data_windows(self):
        del self.data_windows
        self.data_windows = DataWindowList()
        random.seed()
        choices = [500, 500, 1000, 3000, 4000, 5000, 7000, 10000]
        i = 0
        size = self.data.data_size()
        while i < size:
            win = random.choice(choices)
            if (i + win) < size:
                self.data_windows.add_window(window=SingleDataWindow(i_start=i,
                                                                     i_last=i + win,
                                                                     label='hello'))
            i += win

        return

    def set_clean_title(self):
        self.window.set_title(self.title_clean)
        return

    def set_modified_title(self):
        self.window.set_title(self.title_modified)
        return

    def close_application(self, *args):
        self.config.save_config()
        Gtk.main_quit()
        return

    @staticmethod
    def set_spinbutton_defaults(button: Gtk.SpinButton, value: int):
        adjustment = Gtk.Adjustment(step_increment=1, page_increment=10, lower=1, upper=10000)
        button.set_adjustment(adjustment=adjustment)
        button.set_numeric(True)
        button.set_update_policy(Gtk.SpinButtonUpdatePolicy.IF_VALID)
        button.set_value(value)
        return

    def __init__(self):
        self.config = VizConfig()
        self.config.load_config(filename='config.conf')
        self.STATE = MODE_FIRST_WINDOW
        self.data = WatchData()
        self.opened_filename = None
        self.need_redraw = False
        self.timer = None
        self.data_windows = DataWindowList()

        self.title_clean = 'Smart Watch Visualizer'
        self.title_modified = '* Smart Watch Visualizer (file modified)'
        self.data_modified = False

        self.txt_gps_valid = Gtk.Entry()
        self.txt_gps_valid.set_max_length(max=1)
        self.txt_gps_valid.set_text(text=self.config.gps_valid)
        self.txt_gps_invalid = Gtk.Entry()
        self.txt_gps_invalid.set_max_length(max=1)
        self.txt_gps_invalid.set_text(text=self.config.gps_invalid)

        self.sb_gps_window_size = Gtk.SpinButton()
        self.sb_gps_step_delta_rate = Gtk.SpinButton()
        self.sb_gps_win_size_adj_rate = Gtk.SpinButton()
        self.sb_sen_window_size = Gtk.SpinButton()
        self.sb_sen_step_delta_rate = Gtk.SpinButton()
        self.sb_sen_win_size_adj_rate = Gtk.SpinButton()

        # My main window.
        self.window = Gtk.ApplicationWindow(title=self.title_clean)
        self.window.set_default_size(width=600, height=400)

        self.settings = None
        # self.settings = Gtk.Window(transient_for=self.window,
        #                            destroy_with_parent=True,
        #                            title='Edit Settings')
        self.labels_win = None
        self.lbl_labels = Gtk.Label(label='Label Window')
        self.lbl_labels.set_justify(Gtk.Justification.LEFT)
        self.scrolled_win = Gtk.ScrolledWindow()
        self.scrolled_win.add(self.lbl_labels)

        # Create boxes for packing self.window.
        self.vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                             spacing=1)
        self.hbox1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                             spacing=1)

        # Create the menu for the visualizer.
        main = Gio.Menu.new()
        self.menu_bar = Gtk.MenuBar()
        # File menu.
        self.file_menu = Gtk.Menu()
        self.file_item = Gtk.MenuItem(label='File')
        self.open_file_item = Gtk.MenuItem(label='Open File')
        self.open_file_item.set_sensitive(True)
        self.save_item = Gtk.MenuItem(label='Save')
        self.save_item.set_sensitive(False)
        self.save_as_item = Gtk.MenuItem(label='Save As')
        self.save_as_item.set_sensitive(False)

        self.file_menu.append(self.open_file_item)
        self.file_menu.append(Gtk.SeparatorMenuItem())
        self.file_menu.append(self.save_item)
        self.file_menu.append(self.save_as_item)

        self.file_item.set_submenu(self.file_menu)

        self.menu_bar.append(self.file_item)

        # Edit menu
        self.edit_menu = Gtk.Menu()
        self.edit_item = Gtk.MenuItem(label='Edit')
        self.settings_item = Gtk.MenuItem(label='Settings')
        self.settings_item.set_sensitive(True)

        self.edit_menu.append(self.settings_item)

        self.edit_item.set_submenu(self.edit_menu)

        self.menu_bar.append(self.edit_item)

        # Mode menu
        self.mode_menu = Gtk.Menu()
        self.mode_item = Gtk.MenuItem(label='Mode')
        self.mode_gps_item = Gtk.RadioMenuItem(label='GPS Plot')
        self.mode_gps_item.set_active(True)
        self.mode_gps_item.set_sensitive(False)
        self.mode_sensor_item = Gtk.RadioMenuItem(label='Sensors Plot',
                                                  group=self.mode_gps_item)
        self.mode_sensor_item.set_sensitive(False)
        self.mode_annotation_item = Gtk.RadioMenuItem(label='Annotation Help',
                                                      group=self.mode_gps_item)
        self.mode_annotation_item.set_sensitive(False)

        self.mode_menu.append(self.mode_gps_item)
        self.mode_menu.append(self.mode_sensor_item)
        self.mode_menu.append(self.mode_annotation_item)

        self.mode_item.set_submenu(self.mode_menu)

        self.menu_bar.append(self.mode_item)

        self.lbl_progress_start = Gtk.Label(label=str(datetime.datetime.now()))
        self.lbl_progress_start.set_justify(Gtk.Justification.LEFT)
        self.lbl_progress_current = Gtk.Label(label=str(datetime.datetime.now()))
        self.lbl_progress_current.set_justify(Gtk.Justification.CENTER)
        self.lbl_progress_end = Gtk.Label(label=str(datetime.datetime.now()))
        self.lbl_progress_end.set_justify(Gtk.Justification.RIGHT)

        self.hbox1.pack_start(self.lbl_progress_start, True, True, 0)
        self.hbox1.pack_start(self.lbl_progress_current, True, True, 0)
        self.hbox1.pack_start(self.lbl_progress_end, True, True, 0)

        self.progress = Gtk.ProgressBar()
        self.progress.set_fraction(0.0)

        self.eventbox = Gtk.EventBox()
        self.eventbox.add(self.progress)

        self.spinner = Gtk.Spinner()
        self.lbl_loading_file = Gtk.Label(label='Loading file...')
        self.lbl_loading_file.set_justify(Gtk.Justification.LEFT)

        self.window.add(self.vbox1)
        self.vbox1.pack_start(self.menu_bar, False, True, 0)
        self.vbox1.pack_start(self.hbox1, False, True, 0)
        self.vbox1.pack_start(self.eventbox, False, True, 0)
        self.vbox1.pack_start(self.spinner, True, True, 0)
        self.vbox1.pack_start(self.lbl_loading_file, True, True, 0)

        # Matplotlib stuff
        fig = Figure(figsize=(32, 32),
                     layout='tight')

        self.canvas = FigureCanvas(fig)  # a Gtk.DrawingArea
        self.vbox1.pack_start(self.canvas, True, True, 0)
        self.ax = fig.add_subplot()
        self.ax.set_axis_off()

        fig2 = Figure(figsize=(32, 32))
        self.canvas2 = FigureCanvas(fig2)
        self.vbox1.pack_start(self.canvas2, True, True, 0)
        self.axes1 = fig2.add_subplot(3, 1, 1)
        self.axes2 = fig2.add_subplot(3, 1, 2)
        self.axes3 = fig2.add_subplot(3, 1, 3)
        fig2.subplots_adjust(hspace=0)

        self.status_bar = Gtk.Statusbar()
        self.vbox1.pack_start(self.status_bar, False, True, 0)

        self.window.connect('destroy', self.close_application)
        self.window.connect('key-press-event', self.on_key_press_event)
        self.open_file_item.connect('activate', self.on_file_open_clicked)
        self.save_item.connect('activate', self.on_file_save_clicked)
        self.save_as_item.connect('activate', self.on_file_save_as_clicked)
        self.settings_item.connect('activate', self.on_edit_settings_clicked)
        self.mode_gps_item.connect('toggled', self.on_mode_toggled, MODE_GPS_VISUALIZATION)
        self.mode_sensor_item.connect('toggled', self.on_mode_toggled, MODE_SENSOR_VISUALIZATION)
        self.mode_annotation_item.connect('toggled', self.on_mode_toggled, MODE_ANNOTATION_HELP)
        self.eventbox.connect('button-press-event', self.on_button_pressed_progress)
        self.window.show_all()
        self.update_visible_state()
        return


if __name__ == "__main__":
    viz = SmartWatchVisualizer()
    Gtk.main()

