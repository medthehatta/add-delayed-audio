#!/usr/bin/python


"""Take two input signals, add a delay to one, and sum them."""


from __future__ import (
    print_function,  unicode_literals,  division,
)


import sys


from hashlib import sha1


import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
Gst.init(sys.argv)


#
# Helpers
#


def _hash(data):
    """A hash of data."""
    return sha1(str(data)).hexdigest()


def audio_device_source(name, device='default'):
    """An audio source coming from a device."""
    source = Gst.ElementFactory.make('alsasrc', name)
    source.set_property('device', device)
    return source


def queue_with_delay(name, delay=0):
    """A queue that introduces a delay."""
    queue = Gst.ElementFactory.make('queue', name)
    queue.set_property("max-size-time", 0)
    queue.set_property("max-size-buffers", 0)
    queue.set_property("max-size-bytes", 0)
    queue.set_property("min-threshold-time", delay)
    # queue.set_property("leaky", "no")
    return queue


def audio_sink(name):
    """An automatic audio sink."""
    sink = Gst.ElementFactory.make('autoaudiosink', name)
    return sink


def mixed_audio(*components):
    """Audio output from ``components`` mixed together."""
    name = _hash(components)
    mixer = Gst.ElementFactory.make('audiomixer', name)
    for (i, component) in enumerate(components):
        component_out_pad = component.get_static_pad('src')
        mixer_in_pad = mixer.get_request_pad('sink_{}'.format(i))
        component_out_pad.link(mixer_in_pad)
    return mixer


def chain(*components):
    """Link components together."""
    _chain = Gst.Bin(_hash(components))

    _chain.add(*components)

    # The first component's sink is the chain's sink, and the last
    # component's src is the chain's src.
    _chain.add_pad(
        Gst.GhostPad(
            'sink',
            components[0].get_static_pad('sink'),
            direction=Gst.PadDirection.SINK,
        ),
    )
    _chain.add_pad(
        Gst.GhostPad(
            'src',
            components[-1].get_static_pad('src'),
            direction=Gst.PadDirection.SRC,
        ),
    )

    # If we have fewer than 2 components, we're done
    if len(components) < 2:
        return _chain

    # If we have more than 1 component, link them together
    previous_component = components[0]
    for component in components[1:]:
        previous_component.link(component)
        previous_component = component

    return _chain


def pipeline(*components):
    """Assemble a gstreamer pipeline of components."""
    _pipeline = Gst.Pipeline('mypipeline')
    _pipeline.add(chain(*components))
    return _pipeline


def main():
    # Read the command line args to get the delay
    try:
        delay = int(float(sys.argv[1]) * 1e9)
    except IndexError:
        delay = 0
    print('Delay: {}'.format(delay))

    # Set up the pipeline
    my_pipeline = pipeline(
        mixed_audio(
            chain(
                audio_device_source('audiotestsrc', 'default'),
                queue_with_delay('queue', 0),
            ),
            chain(
                audio_device_source('audiotestsrc', 'default'),
                queue_with_delay('queue', delay),
            ),
        ),
        audio_sink('sink'),
    )

    # Begin Playing
    my_pipeline.set_state(Gst.State.PLAYING)


if __name__ == '__main__':
    main()
