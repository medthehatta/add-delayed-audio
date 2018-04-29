#!/usr/bin/python


from __future__ import (
    print_function,  unicode_literals,  division,
)


import pygst
pygst.require("0.10")

import gst
import pygtk
import gtk
import sys


class Main(object):

    def __init__(self):
        """Initialize."""

        # This just reads the command line args
        try:
            delay = int(float(sys.argv[1]) * 1e9)
        except IndexError:
            delay = 0

        print('Delay: {}'.format(delay))

        self.delay_pipeline = gst.Pipeline("mypipeline")

        # ALSA
        self.audiosrc = gst.element_factory_make("alsasrc",  "audio")
        self.audiosrc.set_property("device", "default")
        self.delay_pipeline.add(self.audiosrc)

        # Queue
        self.audioqueue = gst.element_factory_make("queue", "queue1")
        self.audioqueue.set_property("max-size-time", 0)
        self.audioqueue.set_property("max-size-buffers", 0)
        self.audioqueue.set_property("max-size-bytes", 0)
        self.audioqueue.set_property("min-threshold-time", delay)
        self.audioqueue.set_property("leaky", "no")
        self.delay_pipeline.add(self.audioqueue)

        # Audio Output
        self.sink = gst.element_factory_make("autoaudiosink",  "sink")
        self.delay_pipeline.add(self.sink)

        # Link the elements
        self.audiosrc.link(self.audioqueue)
        self.audioqueue.link(self.sink)

        # Begin Playing
        self.delay_pipeline.set_state(gst.STATE_PLAYING)


if __name__ == '__main__':
    start = Main()
    gtk.main()
