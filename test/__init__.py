import io
import os
import sys
from functools import wraps

import six
import tweak

import hca

if 'DEPLOYMENT_STAGE' not in os.environ:
    os.environ['DEPLOYMENT_STAGE'] = 'test'


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


def reset_tweak_changes(f):
    @wraps(f)
    def save_and_restore_tweak_config(*args, **kwargs):
        config = tweak.Config(hca.TWEAK_PROJECT_NAME)
        backup = {}
        for key in config:
            backup[key] = config[key]
        try:
            f(*args, **kwargs)
        finally:
            # Reload config after changes made.
            config = tweak.Config(hca.TWEAK_PROJECT_NAME, autosave=True, save_on_exit=False)
            for key in list(config.keys()):
                del config[key]
            for key, value in backup.items():
                config[key] = value
            config.save()
    return save_and_restore_tweak_config
