#!/usr/bin/python


"""Take two input signals, add a delay to one, and sum them."""


from __future__ import (
    print_function,  unicode_literals,  division,
)


from hashlib import sha1


import gi
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gst, GObject, Gtk
Gst.init(None)


#
# Helpers
#


def _hash(data):
    """A hash of data."""
    return sha1(str(data)).hexdigest()


#
# Sources
#


def audio_device_source(name, device='default'):
    """An audio source coming from a device."""
    source = Gst.ElementFactory.make('alsasrc', name)
    source.set_property('device', device)
    return source


def audio_test_source(name):
    """An audio test source."""
    source = Gst.ElementFactory.make('audiotestsrc', name)
    return source


#
# Sinks
#


def audio_sink(name):
    """An automatic audio sink."""
    sink = Gst.ElementFactory.make('autoaudiosink', name)
    return sink


def file_sink(name, path):
    """A sink which outputs to a file."""
    sink = Gst.ElementFactory.make('filesink', name)
    sink.set_property('location', path)
    return sink


#
# Queue
#


def queue_with_delay(name, delay=0):
    """A queue that introduces a delay."""
    delay_ns = int(delay * 1e9)
    queue = Gst.ElementFactory.make('queue', name)
    queue.set_property('max-size-time', 0)
    queue.set_property('max-size-buffers', 0)
    queue.set_property('max-size-bytes', 0)
    queue.set_property('min-threshold-time', delay_ns)
    # FIXME: this property doesn't seem to work?
    # queue.set_property('leaky', 'no')
    return queue


#
# Combinations
#


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
    """A chain of components linked together end-to-end."""
    _chain = Gst.Bin(_hash(components))

    _chain.add(*components)

    # The first component's sink is the chain's sink, and the last
    # component's src is the chain's src.
    _chain.add_pad(
        Gst.GhostPad(
            'sink',
            target=components[0].get_static_pad('sink'),
            direction=Gst.PadDirection.SINK,
        ),
    )
    _chain.add_pad(
        Gst.GhostPad(
            'src',
            target=components[-1].get_static_pad('src'),
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


#
# Entry point
#


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d',
        '--delay',
        default=0,
        type=float,
        help='Signal delay.',
    )
    parsed = parser.parse_args()

    delay = parsed.delay
    print('Delay: {}'.format(delay))

    # Set up the pipeline
    my_pipeline = pipeline(
        mixed_audio(
            chain(
                audio_test_source('test1'),
                queue_with_delay('queue1', delay),
            ),
        ),
        audio_sink('sink'),
    )

    # Begin Playing
    my_pipeline.set_state(Gst.State.PLAYING)


# --- gtk crap; no need to mess with this stuff below ---


class Main(object):
    """Gtk class required for using gstreamer."""

    def __init__(self):
        main()


if __name__ == '__main__':
    # Start the pipeline
    start = Main()
    Gtk.main()
