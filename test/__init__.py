import io
import os
import sys
import pickle
from functools import wraps

import hca, hca.config
from hca.util.compat import USING_PYTHON2

if 'DEPLOYMENT_STAGE' not in os.environ:
    os.environ['DEPLOYMENT_STAGE'] = 'test'


class CapturingIO:
    def __init__(self, stream_name='stdout'):
        self.stream_name = stream_name
        if USING_PYTHON2:
            from cStringIO import StringIO
            self.buffer = StringIO()
        else:
            self.buffer = io.TextIOWrapper(io.BytesIO(), sys.stdout.encoding)
        self.orig_stream = getattr(sys, stream_name)

    def __enter__(self):
        setattr(sys, self.stream_name, self.buffer)
        return self

    def __exit__(self, *args):
        setattr(sys, self.stream_name, self.orig_stream)

    def captured(self):
        self.buffer.seek(0, io.SEEK_SET)
        return self.buffer.read()


class TweakResetter:
    """
    May be used with 'with', in the decorator (below) or manually:
    """

    def __enter__(self):
        self.save_config()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.restore_config()

    def save_config(self):
        config = hca.get_config()
        self.backup = pickle.dumps(config)

    def restore_config(self):
        # The save method of the previous config manager will be called as an atexit handler.
        # Invalidate its config file path so it fails to save the old config.
        hca.config._config._user_config_home = "/tmp"
        # Reload config after changes made.
        hca.config._config = pickle.loads(self.backup)
        hca.get_config().save()


def reset_tweak_changes(f):
    @wraps(f)
    def save_and_restore_tweak_config(*args, **kwargs):
        with TweakResetter():
            f(*args, **kwargs)
    return save_and_restore_tweak_config
