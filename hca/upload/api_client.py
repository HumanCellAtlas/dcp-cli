import json

import requests

from .upload_config import UploadConfig


class ApiClient:

    def __init__(self, deployment_stage):
        self.api_url_base = UploadConfig().upload_service_api_url_template.format(deployment_stage=deployment_stage)

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
