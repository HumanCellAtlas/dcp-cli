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
        config = hca.get_config()
        backup = pickle.dumps(config)
        try:
            f(*args, **kwargs)
        finally:
            # The save method of the previous config manager will be called as an atexit handler.
            # Invalidate its config file path so it fails to save the old config.
            hca._config._user_config_home = "/tmp"
            # Reload config after changes made.
            hca._config = pickle.loads(backup)
            hca.get_config().save()
    return save_and_restore_tweak_config
