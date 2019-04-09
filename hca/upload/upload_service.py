from . import UploadAreaURI, UploadArea, UploadConfig
from .lib.api_client import ApiClient


class UploadService:

    """
    UploadService is the starting point for the Upload Service API Library.
    """

    def __init__(self, deployment_stage='prod', api_token=None):
        """
        :param str deployment_stage: is normally gleaned from the URI of the Upload Area we are manipulating.
        :param api_token: API key required to perform some operations (create_area).
        """
        self.deployment_stage = deployment_stage
        self.api_token = api_token
        self.api_client = ApiClient(deployment_stage=self.deployment_stage,
                                    authentication_token=self.api_token)

    @staticmethod
    def config():
        """
        :return: Upload Service configuration data
        :rtype: UploadConfig
        """
        return UploadConfig()

    def create_area(self, area_uuid):
        """
        Create an Upload Area
        :param area_uuid: UUID of Upload Area to be created
        :return: an Upload Area object
        :rtype: UploadArea
        """
        result = self.api_client.create_area(area_uuid=area_uuid)
        area_uri = UploadAreaURI(uri=result['uri'])
        return UploadArea(uri=area_uri, upload_service=self)

    def upload_area(self, area_uri):
        """
        Initialize an UploadArea object.  Note this does not create an Upload Area.
        :param UploadAreaURI area_uri: URI of Upload Area
        :return: Upload Area object
        :rtype: UploadArea
        """
        return UploadArea(uri=area_uri, upload_service=self)
