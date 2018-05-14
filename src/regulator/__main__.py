#!/usr/bin/env python3

import os
import signal
import sys

import click
import gi
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import Gtk

from . import decode
from . import parse

gi.require_version('Gtk', '3.0')


class DecoderMonitor:
    def __init__(self, filename):
        self.filename = filename
        self.file = Gio.File.new_for_path(filename)
        self.monitor = self.file.monitor_file(
                Gio.FileMonitorFlags.NONE,
                None)
        self.monitor.connect('changed', self.on_change)
        print('monitoring layout {}'.format(filename))
        self.decoder = decode.Decoder(filename)
        print('decoder loaded')

    def reload(self):
        self.decoder.reload()
        print('decoder reloaded')

    def on_change(self, file_monitor, file, other_file, event_type):
        if event_type == Gio.FileMonitorEvent.CREATED:
            pass
        elif event_type == Gio.FileMonitorEvent.DELETED:
            pass
        elif event_type == Gio.FileMonitorEvent.CHANGED:
            pass
        elif event_type == Gio.FileMonitorEvent.CHANGES_DONE_HINT:
            self.reload()
        elif event_type == Gio.FileMonitorEvent.ATTRIBUTE_CHANGED:
            pass
        else:
            print(self, event_type)

class ClipboardHandler:
    def __init__(self, decoder):
        self.decoder = decoder
        self.parser = parse.Parser()
        print('parser started')
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY,)
        self.clipboard.connect('owner-change', self.on_change)
        print('monitoring primary selection')

    def on_change(self, clipboard, _):
        text = clipboard.wait_for_text()
        if text is None:
            return
        for ms in self.parser.parse_dirty(text):
            self.decoder.decode(ms)
        print('selection done')

class LogHandler:
    def __init__(self, decoder, filename):
        self.decoder = decoder
        self.filename = filename
        self.parser = parse.Parser()
        print('parser started')
        self.file = Gio.File.new_for_path(filename)
        self.monitor = self.file.monitor_file(
                Gio.FileMonitorFlags.NONE,
                None)
        self.monitor.connect('changed', self.on_change)
        print('monitoring file {}'.format(filename))
        self.open()

    def open(self):
        try:
            self.reader = open(self.filename, 'r')
            self.reader.seek(0, os.SEEK_END)
            self.offset = self.reader.tell()
            self.buffer = ''
            print('opened file {}'.format(self.filename))
        except FileNotFoundError:
            self.reader = None

    def close(self):
        try:
            self.reader.close()
            print('closed file {}'.format(self.filename))
        finally:
            self.reader = None

    def read(self):
        self.reader.seek(0, os.SEEK_END)
        if self.offset > self.reader.tell():
            self.close()
            self.open()
        else:
            self.reader.seek(self.offset)
        while True:
            chunk = self.reader.read(4096)
            if not chunk:
                break
            self.buffer += chunk
        self.offset = self.reader.tell()
        lines = self.buffer.split('\n')
        self.buffer = lines.pop()
        if not lines:
            return
        for ms in self.parser.parse_lines(lines):
            self.decoder.decode(ms)

    def on_change(self, file_monitor, file, other_file, event_type):
        if event_type == Gio.FileMonitorEvent.CREATED:
            self.open()
        elif event_type == Gio.FileMonitorEvent.DELETED:
            self.close()
        elif event_type == Gio.FileMonitorEvent.CHANGED:
            if self.reader:
                self.read()
        elif event_type == Gio.FileMonitorEvent.CHANGES_DONE_HINT:
            print('log done')
        else:
            print(self, event_type)

@click.group()
def cli():
    pass

@cli.command()
@click.argument('layout', type=click.Path())
def selection(layout):
    decoder_monitor = DecoderMonitor(layout)
    handler = ClipboardHandler(decoder_monitor.decoder)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    Gtk.main()

@cli.command()
@click.argument('layout', type=click.Path())
@click.argument('log', type=click.Path())
def log(layout, log):
    decoder_monitor = DecoderMonitor(layout)
    handler = LogHandler(decoder_monitor.decoder, 'log.txt')
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    Gtk.main()

if __name__=="__main__":
    cli()
