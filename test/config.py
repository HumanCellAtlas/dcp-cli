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
        # Reload config after changes made.
        config = Config(constants.Constants.TWEAK_PROJECT_NAME, autosave=True, save_on_exit=False)

        new_config_keys = set(config.keys())
        old_config_keys = set(backup.keys())
        added_config_keys = new_config_keys.difference(old_config_keys)

        for key in added_config_keys:
            del config[key]

        for key, value in backup.items():
            config[key] = value
