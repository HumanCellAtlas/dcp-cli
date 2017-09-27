import io, sys

import six


class CapturingIO:
    def __init__(self, stream_name='stdout'):
        self.stream_name = stream_name
        self.buffer = six.StringIO()
        self.orig_stream = getattr(sys, stream_name)

    def __enter__(self):
        setattr(sys, self.stream_name, self.buffer)
        return self

    def __exit__(self, *args):
        setattr(sys, self.stream_name, self.orig_stream)

    def captured(self):
        self.buffer.seek(0, io.SEEK_SET)
        return self.buffer.read()
