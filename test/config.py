import os
from contextlib import contextmanager

from tweak import Config

from hca import constants


@contextmanager
def override_oauth_config():
    config = Config(constants.Constants.TWEAK_PROJECT_NAME)
    backup = {}
    for key in config:
        backup[key] = config[key]
    try:
        yield
    finally:
        for key, value in backup.items():
            config[key] = value
