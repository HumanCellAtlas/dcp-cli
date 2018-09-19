import json

import requests

from .upload_config import UploadConfig


class ApiClient:

    def __init__(self, deployment_stage):
        self.api_url_base = self._api_url(deployment_stage=deployment_stage)

    def files_info(self, area_uuid, file_list):
        url = "{api_url_base}/area/{uuid}/files_info".format(api_url_base=self.api_url_base, uuid=area_uuid)
        response = requests.put(url, data=(json.dumps(file_list)))
        if not response.ok:
            raise RuntimeError(
                "PUT {url} returned {status}, {content}".format(
                    url=url,
                    status=response.status_code,
                    content=response.content))
        return response.json()

    def credentials(self, area_uuid):
        url = "{api_url_base}/area/{uuid}/credentials".format(api_url_base=self.api_url_base, uuid=area_uuid)
        response = requests.post(url)
        if not response.status_code == requests.codes.created:
            raise RuntimeError(
                "POST {url} returned {status}, {content}".format(
                    url=url,
                    status=response.status_code,
                    content=response.content))
        return response.json()

    def checksum_status(self, area_uuid, filename):
        url = "{api_url_base}/area/{uuid}/{filename}/checksum".format(api_url_base=self.api_url_base, uuid=area_uuid,
                                                                      filename=filename)
        return self._get(url)

    def checksum_statuses(self, area_uuid):
        url = "{api_url_base}/area/{uuid}/checksums".format(api_url_base=self.api_url_base, uuid=area_uuid)
        return self._get(url)

    def validation_status(self, area_uuid, filename):
        url = "{api_url_base}/area/{uuid}/{filename}/validate".format(api_url_base=self.api_url_base, uuid=area_uuid,
                                                                      filename=filename)
        return self._get(url)

    def validation_statuses(self, area_uuid):
        url = "{api_url_base}/area/{uuid}/validations".format(api_url_base=self.api_url_base, uuid=area_uuid)
        return self._get(url)

    def _api_url(self, deployment_stage):
        if deployment_stage == 'prod':
            return UploadConfig().production_api_url
        else:
            return UploadConfig().preprod_api_url_template.format(deployment_stage=deployment_stage)

    def _get(self, url):
        response = requests.get(url)
        if not response.ok:
            raise RuntimeError(
                "GET {url} returned {status}, {content}".format(
                    url=url,
                    status=response.status_code,
                    content=response.content))
        return response.json()
