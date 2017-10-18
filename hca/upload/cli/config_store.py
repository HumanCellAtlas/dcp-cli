import tweak

from ... import TWEAK_PROJECT_NAME


class ConfigStore:
    """
    Wrapper around Tweak configuration.
    """

    def __init__(self):
        self._load_config()

    def _load_config(self):
        self._config = tweak.Config(TWEAK_PROJECT_NAME)
        if 'upload' not in self._config:
            self._config.upload = {}
        if 'areas' not in self._config.upload:
            self._config.upload.areas = {}

    def areas(self):
        return self._config.upload.areas

    def add_area(self, urn):
        if urn.urn not in self._config.upload.areas:
            self._config.upload.areas[urn.uuid] = urn.urn
        self.save()

    def select_area(self, area_uuid):
        self._config.upload.current_area = area_uuid
        self.save()

    def current_area(self):
        return self._config.upload.current_area

    def save(self):
        self._config.save()
