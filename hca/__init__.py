from __future__ import absolute_import, division, print_function, unicode_literals

import os, logging

import tweak

class HCAConfig(tweak.Config):
    default_config_file = os.path.join(os.path.dirname(__file__), "default_config.json")
    @property
    def config_files(self):
        return [self.default_config_file] + tweak.Config.config_files.fget(self)

    @property
    def user_config_dir(self):
        return os.path.join(self._user_config_home, self._name)


_config = None
def get_config():
    global _config
    if _config is None:
        _config = HCAConfig(__name__)
    return _config


logger = logging.getLogger(__name__)
