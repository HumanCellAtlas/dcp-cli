import re

from .config_store import ConfigStore
from upload_area_urn import UploadAreaURN


class UploadArea:

    @classmethod
    def all(cls):
        return [cls(uuid=uuid) for uuid in ConfigStore().areas()]

    def __init__(self, uuid=None, urn=None):
        if uuid:
            self.uuid = uuid
            self.urn = UploadAreaURN(ConfigStore().areas()[uuid])
        elif urn:
            self.urn = urn
            self.uuid = urn.uuid
            config = ConfigStore()
            config.add_area(urn)
            config.save()
        else:
            raise RuntimeError("you must provide a uuid or URN")

    @property
    def is_selected(self):
        return ConfigStore().current_area() == self.uuid
