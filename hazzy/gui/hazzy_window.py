#!/usr/bin/env python

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

from lxml import etree
from datetime import datetime

from utilities.constants import Paths
from utilities import logger

# Import our own modules
from widget_manager import WidgetManager
from widget_chooser import WidgetChooser
from screen_chooser import ScreenChooser
from widget_window import WidgetWindow
from screen_stack import ScreenStack
from widget_area import WidgetArea

log = logger.get('HAZZY.WINDOW')

class HazzyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)

        self.widget_manager = WidgetManager()

        self.is_fullscreen = False
        self.is_maximized = False

        gladefile = os.path.join(os.path.dirname(__file__), 'ui', 'hazzy.ui')
        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.builder.connect_signals(self)

        self.connect('window-state-event', self.on_window_state_event)

        self.titlebar = self.builder.get_object('titlebar')
        self.set_titlebar(self.titlebar)

        self.overlay = Gtk.Overlay()
        self.add(self.overlay)

        self.screen_stack = ScreenStack()
        self.overlay.add(self.screen_stack)

        self.widget_chooser = WidgetChooser()
        self.overlay.add_overlay(self.widget_chooser)

        self.screen_chooser = ScreenChooser()
        self.overlay.add_overlay(self.screen_chooser)

        self.set_size_request(900, 600)
        self.show_all()

    def on_show_widget_choser_clicked(self, widget):
        visible = self.widget_chooser.get_visible()
        self.widget_chooser.set_visible(not visible)

    def on_show_screen_choser_clicked(self, widget):
        visible = self.screen_chooser.get_visible()
        self.screen_chooser.set_visible(not visible)

    def on_edit_layout_toggled(self, widget):
        edit = widget.get_active()
        # Hide eventbox used for drag/resize
        screens = self.screen_stack.get_children()
        for screen in screens:
            widgets = screen.get_children()
            for widget in widgets:
                widget.show_overlay(edit)



    def load_from_xml(self):

        if not os.path.exists(Paths.XML_FILE):
            return

        try:
            tree = etree.parse(Paths.XML_FILE)
        except etree.XMLSyntaxError as e:
            error_str = e.error_log.filter_from_level(etree.ErrorLevels.FATAL)
            log.error(error_str)
            return

        root = tree.getroot()

        # Windows (Might support multiple windows in future, so iterate)
        for window in root.iter('window'):
            window_name = window.get('name')
            window_title = window.get('title')

            props = {}
            for prop in window.iterchildren('property'):
                props[prop.get('name')] = prop.text

            self.set_default_size(int(props['w']), int(props['h']))
            self.move(int(props['x']), int(props['y']))
            self.set_maximized(props['maximize'])
            self.set_fullscreen(props['fullscreen'])

            # Add screens
            screens = []
            for screen in window.iter('screen'):
                screen_obj = WidgetArea()
                screen_name = screen.get('name')
                screen_title = screen.get('title')

                self.screen_stack.add_screen(screen_obj, screen_name, screen_title)
                screens.append(screen_name)

                # Add widgets
                for widget in screen.iter('widget'):
                    package = widget.get('package')
                    obj, title, size = self.widget_manager.get_widget(package)
                    wwindow = WidgetWindow(package, obj, title)

                    props = {}
                    for prop in widget.iterchildren('property'):
                        props[prop.get('name')] = prop.text

                    screen_obj.put(wwindow, int(props['x']), int(props['y']))
                    wwindow.set_size_request(int(props['w']), int(props['h']))

        self.screen_chooser.view.fill_iconview(screens)


    def save_to_xml(self):

        # Create XML root element & comment
        root = etree.Element("hazzy_interface")
        root.append(etree.Comment('Interface for: RF45 Milling Machine'))

        # Add time stamp
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        root.append(etree.Comment('Last modified: {}'.format(time_str)))

        # Main window size & position (TODO need to iterate to support multi window)
        win = etree.SubElement(root, "window")
        win.set('name', 'Window 1')
        win.set('title', 'Main Window')

        self.set_property(win, 'maximize', self.is_maximized)
        self.set_property(win, 'fullscreen', self.is_fullscreen)

        x = self.get_position().root_x
        y = self.get_position().root_y
        w = self.get_allocation().width
        h = self.get_allocation().height

        for prop, value in zip(['x','y','w','h'], [x,y,w,h]):
            self.set_property(win, prop, value)

        # Screens
        screens = self.screen_stack.get_children()
        for screen in screens:
            screen_name = self.screen_stack.child_get_property(screen, 'name')
            screen_title = self.screen_stack.child_get_property(screen, 'title')
            screen_pos = self.screen_stack.child_get_property(screen, 'position')

            scr = etree.SubElement(win, "screen")
            scr.set('name', screen_name)
            scr.set('title', screen_title)
            scr.set('position', str(screen_pos))

            # Widgets
            widgets = screen.get_children()
            for widget in widgets:
                wid = etree.SubElement(scr, "widget")
                wid.set('package', widget.package)

                x = screen.child_get_property(widget, 'x')
                y = screen.child_get_property(widget, 'y')
                w = widget.get_size_request().width
                h = widget.get_size_request().height

                for prop, value in zip(['x','y','w','h'], [x,y,w,h]):
                    self.set_property(wid, prop, value)

        with open(Paths.XML_FILE, 'wb') as fh:
            fh.write(etree.tostring(root, pretty_print=True))

# Helpers

    def set_property(self, parent, name, value):
        prop = etree.SubElement(parent, 'property')
        prop.set('name', name)
        prop.text = str(value)

    def set_maximized(self, maximized):
        if maximized == 'True':
            self.maximize()
        else:
            self.unmaximize()

    def set_fullscreen(self, fullscreen):
        if fullscreen == 'True':
            self.fullscreen()
        else:
            self.unfullscreen()

    def on_window_state_event(self, widget, event):

        if event.new_window_state & Gdk.WindowState.FULLSCREEN:
            self.is_fullscreen = bool(event.new_window_state & Gdk.WindowState.FULLSCREEN)

        if event.new_window_state & Gdk.WindowState.MAXIMIZED:
            self.is_maximized = bool(event.new_window_state & Gdk.WindowState.MAXIMIZED)