import re

from .. import get_config
from .exceptions import UploadException
from .upload_area_uri import UploadAreaURI


class UploadConfig:
    """
    Wrapper around Tweak configuration.
    """

    DEFAULT_BUCKET_NAME_TEMPLATE = "org-humancellatlas-upload-{deployment_stage}"
    DEFAULT_PREPROD_API_URL_TEMPLATE = "https://upload.{deployment_stage}.data.humancellatlas.org/v1"
    DEFAULT_PRODUCTION_API_URL = "https://upload.data.humancellatlas.org/v1"

    def __init__(self):
        self._load_config()
        self._set_defaults()

    def _load_config(self):
        self._config = get_config()

    def _set_defaults(self):
        if 'upload' not in self._config:
            self._config.upload = {}
        if 'areas' not in self._config.upload:
            self._config.upload.areas = {}
        if 'current_area' not in self._config.upload:
            self._config.upload.current_area = None
        if 'bucket_name_template' not in self._config.upload:
            self._config.upload.bucket_name_template = self.DEFAULT_BUCKET_NAME_TEMPLATE
        if 'production_api_url' not in self._config.upload:
            self._config.upload.production_api_url = self.DEFAULT_PRODUCTION_API_URL
        if 'preprod_api_url_template' not in self._config.upload:
            self._config.upload.preprod_api_url_template = self.DEFAULT_PREPROD_API_URL_TEMPLATE
        self.save()

    @property
    def areas(self):
        """
        Return list of all known areas
        :return: list of UUIDs
        :rtype: list
        """
        return list(self._config.upload.areas.keys())

    @property
    def current_area(self):
        """
        UploadConfig maintains the concept of a "current" Upload Area.
        This property returns it.
        :return: UUID of current Upload Area
        :rtype: str
        """
        return self._config.upload.current_area

    @property
    def bucket_name_template(self):
        """
        The bucket_name_template may be used with an interpolated variable "deployment_stage"
        to determine the bucket name of an Upload Service deployment.
        :return: bucket name template
        :rtype: str
        """
        return self._config.upload.bucket_name_template

    @property
    def preprod_api_url_template(self):
        """
        The preprod_api_url_template may be used with an interpolated variable "deployment_stage"
        to determine the API base URL of an Upload Service deployment.
        :return: url template
        :rtype: str
        """
        return self._config.upload.preprod_api_url_template

    @property
    def production_api_url(self):
        """
        :return: the currently configured base URL for the production REST API of the Upload Service
        """
        return self._config.upload.production_api_url

    def area_uri(self, area_uuid):
        """
        Return the URI for an Upload Area
        :param area_uuid: UUID of area for which we want URI
        :return: Upload Area URI object
        :rtype: UploadAreaURI
        :raises UploadException: if area does not exist
        """
        if area_uuid not in self.areas:
            raise UploadException("I don't know about area {uuid}".format(uuid=area_uuid))
        return UploadAreaURI(self._config.upload.areas[area_uuid]['uri'])

    def add_area(self, uri):
        """
        Record information about a new Upload Area

        :param UploadAreaURI uri: An Upload Area URI.
        """
        if uri.area_uuid not in self._config.upload.areas:
            self._config.upload.areas[uri.area_uuid] = {'uri': uri.uri}
        self.save()

    def select_area(self, area_uuid):
        """
        Update the "current area" to be the area with this UUID.

        :param str area_uuid: The RFC4122-compliant UUID of the Upload Area.
        """

        self._config.upload.current_area = area_uuid
        self.save()

    def forget_area(self, area_uuid):
        """
        Remove an Upload Area from out cache of known areas.
        :param str area_uuid: The RFC4122-compliant UUID of the Upload Area.
        """
        if self._config.upload.current_area == area_uuid:
            self._config.upload.current_area = None
        if area_uuid in self._config.upload.areas:
            del self._config.upload.areas[area_uuid]
            self.save()

    def area_uuid_from_partial_uuid(self, partial_uuid):
        """
        Given a partial UUID (a prefix), see if we have know about an Upload Area matching it.
        :param (str) partial_uuid: UUID prefix
        :return: a matching UUID
        :rtype: str
        :raises UploadException: if no or more than one UUIDs match.
        """
        matching_areas = [uuid for uuid in self.areas if re.match(partial_uuid, uuid)]
        if len(matching_areas) == 0:
            raise UploadException("Sorry I don't recognize area \"%s\"" % (partial_uuid,))
        elif len(matching_areas) == 1:
            return matching_areas[0]
        else:
            raise UploadException(
                "\"%s\" matches more than one area, please provide more characters." % (partial_uuid,))

    def unique_prefix(self, area_uuid):
        """
        Find the minimum prefix required to address this Upload Area UUID uniquely.
        :param (str) area_uuid: UUID of Upload Area
        :return: a string with the minimum prefix required to be unique
        :rtype: str
        """
        for prefix_len in range(1, len(area_uuid)):
            prefix = area_uuid[0:prefix_len]
            matching_areas = [uuid for uuid in self.areas if re.match(prefix, uuid)]
            if len(matching_areas) == 1:
                return prefix

    def save(self):
        self._config.save()
