#!/usr/bin/env python3

import sys
import signal

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

from . import parse, decode

class Handler:
    def __init__(self, layout):
        self.decoder = decode.Decoder(open(layout))
        print('decoder loaded')
        self.parser = parse.Parser()

    def on_change(self, clipboard, _):
        text = clipboard.wait_for_text()
        if text is None:
            return
        for ms in self.parser.parse(text):
            self.decoder.decode(ms)
        print('done')

def main():
    handler = Handler(sys.argv[1])
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY,)
    clipboard.connect('owner-change', handler.on_change)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    Gtk.main()

if __name__=="__main__":
    main()
