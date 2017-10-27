import re

from .upload_config import UploadConfig
from .upload_area_urn import UploadAreaURN
from .exceptions import UploadException


class UploadArea:

    @classmethod
    def all(cls):
        return [cls(uuid=uuid) for uuid in UploadConfig().areas()]

    @classmethod
    def areas_matching_alias(cls, alias):
        return [cls(uuid=uuid) for uuid in UploadConfig().areas() if re.match(alias, uuid)]

    def __init__(self, **kwargs):
        """
        You must supply either a uuid or urn keyword argument.

        :param uuid: The UUID of an existing Upload Area that we know about.
        :param urn: An UploadAreaURN for a new area.
        """
        if 'uuid' in kwargs:
            self.uuid = kwargs['uuid']
            areas = UploadConfig().areas()
            if self.uuid not in areas:
                raise UploadException("I'm not aware of upload area \"%s\"" % self.uuid)
            self.urn = UploadAreaURN(areas[self.uuid])
        elif 'urn' in kwargs:
            self.urn = kwargs['urn']
            self.uuid = self.urn.uuid
            UploadConfig().add_area(self.urn)
        else:
            raise UploadException("You must provide a uuid or URN")

    @property
    def is_selected(self):
        return UploadConfig().current_area() == self.uuid

    @property
    def unique_prefix(self):
        for prefix_len in range(1, len(self.uuid)):
            prefix = self.uuid[0:prefix_len]
            matches = UploadArea.areas_matching_alias(prefix)
            if len(matches) == 1:
                return prefix

    def select(self):
        config = UploadConfig()
        config.select_area(self.uuid)
