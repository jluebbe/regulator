#!/usr/bin/env python3

import signal

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

from . import memory, parse

def on_change(clipboard, _):
    text = clipboard.wait_for_text()
    if text is None:
        return
    for slice in parse.parse_dump(text):
        print(slice)

def main():
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY,)
    clipboard.connect('owner-change', on_change)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    Gtk.main()

if __name__=="__main__":
    main()
