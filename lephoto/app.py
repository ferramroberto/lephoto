"""Applicazione GTK."""
import sys
from .util import *
from .main_window import Main

class App(Gtk.Application):
    def __init__(self): super().__init__(application_id="org.lephoto.App")
    def do_activate(self): Main(self).present()

def main():
    sys.exit(App().run(sys.argv))
