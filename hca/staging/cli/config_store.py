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
        if 'staging' not in self._config:
            self._config.staging = {}
        if 'areas' not in self._config.staging:
            self._config.staging.areas = {}

    def areas(self):
        return self._config.staging.areas

    def add_area(self, urn):
        if urn.urn not in self._config.staging.areas:
            self._config.staging.areas[urn.uuid] = urn.urn
        self.save()

    def select_area(self, area_uuid):
        self._config.staging.current_area = area_uuid
        self.save()

    def current_area(self):
        return self._config.staging.current_area

    def save(self):
        self._config.save()
