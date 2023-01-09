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
import threading
from matplotlib.backends.backend_gtk3agg import FigureCanvas  # or gtk3cairo.
from numpy.random import random
from matplotlib.figure import Figure
import matplotlib.style as mplstyle
from data import WatchData
from data.config import VizConfig
from data import MODE_GPS, MODE_SENSORS

mplstyle.use(['fast'])

MODE_FIRST_WINDOW = 0
MODE_OPENING_FILE = 1
MODE_GPS_VISUALIZATION = 2
MODE_SAVING_FILE = 3
MODE_SENSOR_VISUALIZATION = 4


class SmartWatchVisualizer:
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
        self.STATE = MODE_GPS_VISUALIZATION
        GLib.idle_add(self.set_status_message, 'Ready')
        GLib.idle_add(self.set_all_lbl_progress)
        GLib.idle_add(self.update_visible_state)
        GLib.idle_add(self.draw_canvas)
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
        if self.STATE == MODE_GPS_VISUALIZATION:
            GLib.idle_add(self.draw_canvas_next)
        else:
            self.draw_canvas_next()
        return

    def draw_canvas_next(self):
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
            print('draw for sensors')
            self.axes1.cla()
            self.axes2.cla()
            self.axes3.cla()
            self.data.plot_sensors(axis1=self.axes1,
                                   axis2=self.axes2,
                                   axis3=self.axes3)
            self.canvas2.draw_idle()
            self.canvas2.flush_events()
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
        print('key press:  {}'.format(event.string))
        if event.keyval == 65361:       # Left
            print('LEFT')
            if self.data.step_backward():
                GLib.idle_add(self.set_current_lbl_progress)
                if self.STATE == MODE_SENSOR_VISUALIZATION:
                    self.need_redraw = True
                else:
                    GLib.idle_add(self.draw_canvas)
        elif event.keyval == 65363:     # Right
            print('RIGHT')
            if self.data.step_forward():
                GLib.idle_add(self.set_current_lbl_progress)
                if self.STATE == MODE_SENSOR_VISUALIZATION:
                    self.need_redraw = True
                else:
                    GLib.idle_add(self.draw_canvas)
        elif event.keyval == 65362:     # Up
            print('UP')
            if self.data.increase_window_size():
                GLib.idle_add(self.set_first_current_lbl_progress)
                if self.STATE == MODE_SENSOR_VISUALIZATION:
                    self.need_redraw = True
                else:
                    GLib.idle_add(self.draw_canvas)
        elif event.keyval == 65364:     # Down
            print('DOWN')
            if self.data.decrease_window_size():
                GLib.idle_add(self.set_first_current_lbl_progress)
                if self.STATE == MODE_SENSOR_VISUALIZATION:
                    self.need_redraw = True
                else:
                    GLib.idle_add(self.draw_canvas)
        elif self.STATE == MODE_GPS_VISUALIZATION:
            if event.string == self.config.gps_invalid:
                print(self.config.gps_invalid)
                self.data.mark_window_invalid()
                GLib.idle_add(self.draw_canvas)
            elif event.string == self.config.gps_valid:
                print(self.config.gps_valid)
                self.data.mark_window_valid()
                GLib.idle_add(self.draw_canvas)
        elif self.STATE == MODE_SENSOR_VISUALIZATION:
            if event.string in self.config.annotations.keys():
                self.data.annotate_window(annotation=self.config.annotations[event.string])
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
        return

    def on_mode_toggled(self, widget, mode):
        if widget.get_active():
            self.STATE = mode
            if self.STATE == MODE_GPS_VISUALIZATION:
                self.data.set_mode(mode=MODE_GPS)
            elif self.STATE == MODE_SENSOR_VISUALIZATION:
                self.data.set_mode(mode=MODE_SENSORS)
                self.timer = GLib.timeout_add(100, self.timer_tick)
            self.need_redraw = True
            self.update_visible_state()
            GLib.idle_add(self.set_all_lbl_progress)
            GLib.idle_add(self.draw_canvas)
        return

    def close_application(self, *args):
        self.config.save_config()
        Gtk.main_quit()
        return

    def __init__(self):
        self.config = VizConfig()
        self.config.load_config(filename='config.conf')
        self.STATE = MODE_FIRST_WINDOW
        self.data = WatchData()
        self.opened_filename = None
        self.need_redraw = False
        self.timer = None
        # My main window.
        self.window = Gtk.ApplicationWindow(title='Smart Watch Visualizer')
        self.window.set_default_size(width=600, height=400)

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
        # Mode menu
        self.mode_menu = Gtk.Menu()
        self.mode_item = Gtk.MenuItem(label='Mode')
        self.mode_gps_item = Gtk.RadioMenuItem(label='GPS Plot')
        self.mode_gps_item.set_active(True)
        self.mode_gps_item.set_sensitive(False)
        self.mode_sensor_item = Gtk.RadioMenuItem(label='Sensors Plot',
                                                  group=self.mode_gps_item)
        self.mode_sensor_item.set_sensitive(False)

        self.file_menu.append(self.open_file_item)
        self.file_menu.append(Gtk.SeparatorMenuItem())
        self.file_menu.append(self.save_item)
        self.file_menu.append(self.save_as_item)

        self.file_item.set_submenu(self.file_menu)

        self.menu_bar.append(self.file_item)

        self.mode_menu.append(self.mode_gps_item)
        self.mode_menu.append(self.mode_sensor_item)

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
        self.mode_gps_item.connect('toggled', self.on_mode_toggled, MODE_GPS_VISUALIZATION)
        self.mode_sensor_item.connect('toggled', self.on_mode_toggled, MODE_SENSOR_VISUALIZATION)
        self.eventbox.connect('button-press-event', self.on_button_pressed_progress)
        self.window.show_all()
        self.update_visible_state()
        return


if __name__ == "__main__":
    viz = SmartWatchVisualizer()
    Gtk.main()

