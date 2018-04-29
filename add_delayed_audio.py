#!/usr/bin/python


"""Take two input signals, add a delay to one, and sum them."""


from __future__ import (
    print_function,  unicode_literals,  division,
)


import pygst
pygst.require("0.10")

import gst
import pygtk
import gtk
import sys


def audio_device_source(name, device='default'):
    """An audio source coming from a device."""
    source = gst.element_factory_make('alsasrc', name)
    source.set_property('device', device)
    return source


def queue_with_delay(name, delay=0):
    """A queue that introduces a delay."""
    queue = gst.element_factory_make('queue', name)
    queue.set_property("max-size-time", 0)
    queue.set_property("max-size-buffers", 0)
    queue.set_property("max-size-bytes", 0)
    queue.set_property("min-threshold-time", delay)
    queue.set_property("leaky", "no")
    return queue


def audio_sink(name):
    """An automatic audio sink."""
    sink = gst.element_factory_make('autoaudiosink', name)
    return sink


def pipeline(*components):
    """Assemble a gstreamer pipeline of components."""
    _pipeline = gst.Pipeline('mypipeline')

    for component in components:
        _pipeline.add(component)

    # If we have fewer than 2 components, we're done
    if len(components) < 2:
        return _pipeline

    # If we have more than 1 component, link them together
    previous_component = components[0]
    for component in components[1:]:
        previous_component.link(component)
        previous_component = component

    return _pipeline


class Main(object):
    """The main Gtk+ class running the Gstreamer pipeline."""

    def __init__(self):
        """Initialize."""

        # Read the command line args to get the delay
        try:
            delay = int(float(sys.argv[1]) * 1e9)
        except IndexError:
            delay = 0
        print('Delay: {}'.format(delay))

        # Set up the pipeline
        self.delay_pipeline = pipeline(
            audio_device_source('default'),
            queue_with_delay(delay),
            audio_sink(),
        )

        # Begin Playing
        self.delay_pipeline.set_state(gst.STATE_PLAYING)


if __name__ == '__main__':
    start = Main()
    gtk.main()
