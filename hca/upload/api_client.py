import requests


class ApiClient:

    UPLOAD_SERVICE_API_URL_TEMPLATE = "https://upload.{deployment_stage}.data.humancellatlas.org/v1"

    def __init__(self, deployment_stage):
        self.api_url_base = ApiClient.UPLOAD_SERVICE_API_URL_TEMPLATE.format(deployment_stage=deployment_stage)

    def list_area(self, area_uuid):
        url = "{api_url_base}/area/{uuid}".format(api_url_base=self.api_url_base, uuid=area_uuid)
        response = requests.get(url)
        assert response.ok
        return response.json()['files']
