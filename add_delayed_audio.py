#!/usr/bin/python


"""Take two input signals, add a delay to one, and sum them."""


from __future__ import (
    print_function,  unicode_literals,  division,
)


from hashlib import sha1
from functools import wraps


import gi
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gst
Gst.init(None)


#  Note to the reader: execution begins in the main() function, which is at the
#  bottom of the file.


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


def audio_test_source(name, frequency=400):
    """An audio test source."""
    source = Gst.ElementFactory.make('audiotestsrc', name)
    source.set_property('freq', frequency)
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
# Mixer
#


def audio_mixer(name):
    """An audio mixer."""
    return Gst.ElementFactory.make('audiomixer', name)


#
# Combinations
#


def demux_into(*components, **kwargs):
    """
    Link all the outputs of the ``components`` into ``demuxer``.

    ``demuxer`` must be a component which supports adding multiple "sink_%u"
    pads.
    """
    element = kwargs.get('demuxer')
    for (i, component) in enumerate(components):
        component_out_pad = component.get_static_pad('src')
        new_in_pad = element.get_request_pad('sink_{}'.format(i))
        component_out_pad.link(new_in_pad)


#
# Execution
#


def play_until_interrupt_or_error(pipeline):
    # Begin Playing
    pipeline.set_state(Gst.State.PLAYING)

    # Wait for error or end of signal, then stop the pipeline.
    bus = pipeline.get_bus()
    while True:
        try:
            msg = bus.timed_pop_filtered(
                0.5 * Gst.SECOND,
                Gst.MessageType.ERROR | Gst.MessageType.EOS,
            )
            if msg:
                break
        except KeyboardInterrupt:
            break

    pipeline.set_state(Gst.State.NULL)


#
# Entry point
#


def main():
    # Get the command-line arguments.
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

    # Extract the delay from the arguments.
    delay = parsed.delay
    print('Delay: {}'.format(delay))

    # Declare our pipeline elements.
    source1 = audio_test_source('source1', frequency=100)
    # source1 = audio_device_source('source1', 'hd:0,1')
    source2 = audio_test_source('source2', frequency=100)
    # source2 = audio_device_source('source2', 'hd:1,1')
    delay_queue = queue_with_delay('delay', delay)
    mixer = audio_mixer('mixer')
    sink = audio_sink('sink')

    # Assemble the pipeline.
    pipeline = Gst.Pipeline('pipeline')
    pipeline.add(source1, source2, delay_queue, mixer, sink)

    # Connect the elements in the pipeline.
    #
    # N.B. This MUST be done after the pipeline is assembled (after the
    # `add()`).
    #
    #   source1 --> delay_queue -->|
    #                              |--> mixer --> sink
    #   source2 --------------> -->|
    #
    source1.link(delay_queue)
    demux_into(delay_queue, source2, demuxer=mixer)
    mixer.link(sink)

    play_until_interrupt_or_error(pipeline)


if __name__ == '__main__':
    main()
