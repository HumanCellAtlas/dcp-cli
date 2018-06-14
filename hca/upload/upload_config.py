import six

from .. import get_config

from .upload_area_urn import UploadAreaURN


class UploadConfig:
    """
    Wrapper around Tweak configuration.
    """

    DEFAULT_BUCKET_NAME_TEMPLATE = "org-humancellatlas-upload-{deployment_stage}"
    DEFAULT_UPLOAD_SERVICE_API_URL_TEMPLATE = "https://upload.{deployment_stage}.data.humancellatlas.org/v1"

    def __init__(self):
        self._load_config()
        self._set_defaults()
        self._convert_to_uris()  # Remove in a month or two

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
        if 'upload_service_api_url_template' not in self._config.upload:
            self._config.upload.upload_service_api_url_template = self.DEFAULT_UPLOAD_SERVICE_API_URL_TEMPLATE
        self.save()

    @property
    def areas(self):
        return self._config.upload.areas

    @property
    def current_area(self):
        return self._config.upload.current_area

    @property
    def bucket_name_template(self):
        return self._config.upload.bucket_name_template

    @property
    def upload_service_api_url_template(self):
        return self._config.upload.upload_service_api_url_template

    def add_area(self, uri):
        if uri.area_uuid not in self._config.upload.areas:
            self._config.upload.areas[uri.area_uuid] = {'uri': uri.uri}
        self.save()

    def select_area(self, area_uuid):
        self._config.upload.current_area = area_uuid
        self.save()

    def forget_area(self, area_uuid):
        if self._config.upload.current_area == area_uuid:
            self._config.upload.current_area = None
        if area_uuid in self._config.upload.areas:
            del self._config.upload.areas[area_uuid]
            self.save()

    def save(self):
        self._config.save()

    """
    Convert:
      "areas": {
        "deadbeef-dead-dead-dead-beeeeeeeeef": "dcp:upl:aws:dev:deadbeef-dead-dead-dead-beeeeeeeeeef:ENCRYPTEDCREDS"
      }
      to
      "areas": {
        "deadbeef-dead-dead-dead-beeeeeeeeeef": {
          "uri": "s3://org-humancellatlas-upload-dev/deadbeef-dead-dead-dead-beeeeeeeeeef/"
        }
      }
    """
    def _convert_to_uris(self):
        for area_id, area_data in self.areas.items():
            if isinstance(area_data, six.text_type):
                urn = UploadAreaURN(area_data)
                bucket_name = self.bucket_name_template.format(deployment_stage=urn.deployment_stage)
                self.areas[area_id] = {
                    "uri": "s3://{bucket_name}/{area_id}/".format(bucket_name=bucket_name, area_id=area_id)
                }
        self.save()
