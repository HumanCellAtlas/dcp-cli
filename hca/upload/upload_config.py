from .. import get_config


class UploadConfig:
    """
    Wrapper around Tweak configuration.
    """

    DEFAULT_BUCKET_NAME_TEMPLATE = "org-humancellatlas-upload-{deployment_stage}"
    DEFAULT_UPLOAD_SERVICE_API_URL_TEMPLATE = "https://upload.{deployment_stage}.data.humancellatlas.org/v1"

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
        if 'upload_service_api_url_template' not in self._config.upload:
            self._config.upload.upload_service_api_url_template = self.DEFAULT_UPLOAD_SERVICE_API_URL_TEMPLATE
        self.save()

    def areas(self):
        return self._config.upload.areas

    def add_area(self, urn):
        if urn.urn not in self._config.upload.areas:
            self._config.upload.areas[urn.uuid] = urn.urn
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

    @property
    def current_area(self):
        return self._config.upload.current_area

    @property
    def bucket_name_template(self):
        return self._config.upload.bucket_name_template

    @property
    def upload_service_api_url_template(self):
        return self._config.upload.upload_service_api_url_template

    def save(self):
        self._config.save()
