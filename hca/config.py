import os, logging

from tweak import Config as _Config

class HCAConfig(_Config):
    default_config_file = os.path.join(os.path.dirname(__file__), "default_config.json")

    def __init__(self, *args, **kwargs):
        super(HCAConfig, self).__init__(name="hca", *args, **kwargs)

    @property
    def config_files(self):
        return [self.default_config_file] + _Config.config_files.fget(self)

    @property
    def user_config_dir(self):
        return os.path.join(self._user_config_home, self._name)


_config = None
def get_config():
    global _config
    if _config is None:
        _config = HCAConfig()
    return _config


logger = logging.getLogger("hca")
