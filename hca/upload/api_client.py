import json

import requests


class ApiClient:

    UPLOAD_SERVICE_API_URL_TEMPLATE = "https://upload.{deployment_stage}.data.humancellatlas.org/v1"

    def __init__(self, deployment_stage):
        self.api_url_base = ApiClient.UPLOAD_SERVICE_API_URL_TEMPLATE.format(deployment_stage=deployment_stage)

    def files_info(self, area_uuid, file_list):
        url = "{api_url_base}/area/{uuid}/files_info".format(api_url_base=self.api_url_base, uuid=area_uuid)
        response = requests.put(url, data=(json.dumps(file_list)))
        if not response.ok:
            raise RuntimeError(
                "GET {url} returned {status}, {content}".format(
                    url=url,
                    status=response.status_code,
                    content=response.content))
        return response.json()
