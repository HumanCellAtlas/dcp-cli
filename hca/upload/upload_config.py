import tweak

from .. import TWEAK_PROJECT_NAME


class UploadConfig:
    """
    Wrapper around Tweak configuration.
    """

    DEFAULT_BUCKET_NAME_TEMPLATE = "org-humancellatlas-upload-{deployment_stage}"

    def __init__(self):
        self._load_config()

    def _load_config(self):
        self._config = tweak.Config(TWEAK_PROJECT_NAME, save_on_exit=False)
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
        if 'bucket_name_template' not in self._config.upload:
            self._config.upload.bucket_name_template = self.DEFAULT_BUCKET_NAME_TEMPLATE
            self.save()
        return self._config.upload.bucket_name_template

    def save(self):
        self._config.save()
