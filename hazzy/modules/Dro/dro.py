#!/usr/bin/env python

import os
import sys
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))
UIDIR = os.path.join(PYDIR)
HAZZYDIR = os.path.abspath(os.path.join(PYDIR, '../..'))
if HAZZYDIR not in sys.path:
    sys.path.insert(1, HAZZYDIR)

from utilities import logger
from utilities.status import Status
from utilities.constants import Paths

# Setup logging
log = logger.get("HAZZY.WIDGETS.DRO")


class Dro(Gtk.Box):

    def __init__(self):
        Gtk.Box.__init__(self)

        self.stat = Status

        self.stat.on_value_changed('axis_positions', self.update_dros, False)

        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(UIDIR, 'dro.ui'))

        self.x = self.builder.get_object('x')
        self.y = self.builder.get_object('y')
        self.z = self.builder.get_object('z')

        self.display = self.builder.get_object('dro')

        self.add(self.display)
        self.show_all()

    def update_dros(self, widget, positions):
        pos, rel, dtg = positions
        self.x.set_text(str(rel[0]))
        self.y.set_text(str(rel[1]))
        self.z.set_text(str(rel[2]))