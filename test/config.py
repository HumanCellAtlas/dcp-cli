import os
from contextlib import contextmanager

from tweak import Config

import hca


@contextmanager
def override_oauth_config():
    config = Config(hca.TWEAK_PROJECT_NAME)
    backup = {}
    login = config.get('login', {})
    for key in login:
        backup[key] = login[key]
    try:
        yield
    finally:
        # Reload config after changes made.
        config = Config(hca.TWEAK_PROJECT_NAME, autosave=True, save_on_exit=False)

        config.login = {}

        for key, value in backup.items():
            config.login[key] = value
