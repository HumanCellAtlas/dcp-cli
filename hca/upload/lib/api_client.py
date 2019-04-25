try:
    import urllib.parse as urlparse
except ImportError:
    import urllib as urlparse

import requests
from tenacity import retry, stop_after_attempt, wait_fixed

from ..upload_config import UploadConfig


class UploadApiException(RuntimeError):
    """
    Exception returned if problems are encountered
    """
    pass


class ApiClient:

    """
    The ApiClient knows:
      - which HTTP verb and path to use to execute an action
      - when and how to authenticate

    ApiClient is not normally called directly, it is used by UploadArea.
    """

    def __init__(self, deployment_stage, authentication_token=None):
        self.deployment_stage = deployment_stage
        self.auth_token = authentication_token

    # Upload Area Manipulation

    def create_area(self, area_uuid):
        """
        Create an Upload Area

        :param str area_uuid: A RFC4122-compliant ID for the upload area
        :return: a dict of the form { "uri": "s3://<bucket_name>/<upload-area-id>/" }
        :rtype: dict
        :raises UploadApiException: if the an Upload Area was not created
        """
        response = self._make_request('post',
                                      path="/area/{id}".format(id=area_uuid),
                                      headers={'Api-Key': self.auth_token})
        return response.json()

    def area_exists(self, area_uuid):
        """
        Check if an Upload Area exists

        :param str area_uuid: A RFC4122-compliant ID for the upload area
        :return: True or False
        :rtype: bool
        """
        response = requests.head(self._url(path="/area/{id}".format(id=area_uuid)))
        return response.ok

    def delete_area(self, area_uuid):
        """
        Delete an Upload Area

        :param str area_uuid: A RFC4122-compliant ID for the upload area
        :return: True
        :rtype: bool
        :raises UploadApiException: if the an Upload Area was not deleted
        """
        self._make_request('delete', path="/area/{id}".format(id=area_uuid),
                           headers={'Api-Key': self.auth_token})
        return True

    def credentials(self, area_uuid):
        """
        Get AWS credentials required to directly upload files to Upload Area in S3

        :param str area_uuid: A RFC4122-compliant ID for the upload area
        :return: a dict containing an AWS AccessKey, SecretKey and SessionToken
        :rtype: dict
        :raises UploadApiException: if credentials could not be obtained
        """
        response = self._make_request("post", path="/area/{uuid}/credentials".format(uuid=area_uuid))
        return response.json()

    # Files

    def store_file(self, area_uuid, filename, file_content, content_type):
        """
        Store a small file in an Upload Area

        :param str area_uuid: A RFC4122-compliant ID for the upload area
        :param str filename: The name the file will have in the Upload Area
        :param str file_content: The contents of the file
        :param str content_type: The MIME-type for the file
        :return: information about the stored file (similar to that returned by files_info)
        :rtype: dict
        :raises UploadApiException: if file could not be stored
        """
        url_safe_filename = urlparse.quote(filename)
        path = "/area/{id}/{filename}".format(id=area_uuid, filename=url_safe_filename)
        response = self._make_request('put',
                                      path=path,
                                      data=file_content,
                                      headers={
                                          'Api-Key': self.auth_token,
                                          'Content-Type': content_type
                                      })
        return response.json()

    @retry(reraise=True, wait=wait_fixed(2), stop=stop_after_attempt(3))
    def file_upload_notification(self, area_uuid, filename):
        """
        Notify Upload Service that a file has been placed in an Upload Area

        :param str area_uuid: A RFC4122-compliant ID for the upload area
        :param str filename: The name the file in the Upload Area
        :return: True
        :rtype: bool
        :raises UploadApiException: if file could not be stored
        """
        url_safe_filename = urlparse.quote(filename)
        path = ("/area/{area_uuid}/{filename}".format(area_uuid=area_uuid, filename=url_safe_filename))
        response = self._make_request('post', path=path)
        return response.ok

    def files_info(self, area_uuid, file_list):
        """
        Get information about files

        :param str area_uuid: A RFC4122-compliant ID for the upload area
        :param list file_list: The names the files in the Upload Area about which we want information
        :return: an array of file information dicts
        :rtype: list of dicts
        :raises UploadApiException: if information could not be obtained
        """
        path = "/area/{uuid}/files_info".format(uuid=area_uuid)
        file_list = [urlparse.quote(filename) for filename in file_list]
        response = self._make_request('put', path=path, json=file_list)
        return response.json()

    # Checksumming

    def checksum_status(self, area_uuid, filename):
        """
        Retrieve checksum status and values for a file

        :param str area_uuid: A RFC4122-compliant ID for the upload area
        :param str filename: The name of the file within the Upload Area
        :return: a dict with checksum information
        :rtype: dict
        :raises UploadApiException: if information could not be obtained
        """
        url_safe_filename = urlparse.quote(filename)
        path = "/area/{uuid}/{filename}/checksum".format(uuid=area_uuid, filename=url_safe_filename)
        response = self._make_request('get', path)
        return response.json()

    def checksum_statuses(self, area_uuid):
        """
        Retrieve counts of files in Upload Area in each checksumming state: scheduled for checksumming, checksumming,
        checksummed, and unscheduled.

        :param str area_uuid: A RFC4122-compliant ID for the upload area
        :return: a dict with key for each state and value being the count of files in that state
        :rtype: dict
        :raises UploadApiException: if information could not be obtained
        """
        path = "/area/{uuid}/checksums".format(uuid=area_uuid)
        result = self._make_request('get', path)
        return result.json()

    # Validation

    def validate_files(self, area_uuid, file_list, validator_image, original_validation_id="", environment={}):
        """
        Invoke supplied validator Docker image and give it access to the file/s.
        The validator must be based off the base validator Docker image.

        :param str area_uuid: A RFC4122-compliant ID for the upload area
        :param list file_list: A list of files within the Upload Area to be validated
        :param str validator_image: the location of a docker image to use for validation
        :param str original_validation_id: [optional]
        :param dict environment: [optional] list of environment variable to set for the validator
        :return: ID of scheduled validation
        :rtype: dict
        :raises UploadApiException: if information could not be obtained
        """
        path = "/area/{uuid}/validate".format(uuid=area_uuid)
        file_list = [urlparse.quote(filename) for filename in file_list]
        payload = {
            "environment": environment,
            "files": file_list,
            "original_validation_id": original_validation_id,
            "validator_image": validator_image
        }
        result = self._make_request('put', path=path, json=payload, headers={'Api-Key': self.auth_token})
        return result.json()

    def validation_status(self, area_uuid, filename):
        """
        Get status and results of latest validation job for a file.

        :param str area_uuid: A RFC4122-compliant ID for the upload area
        :param str filename: The name of the file within the Upload Area
        :return: a dict with validation information
        :rtype: dict
        :raises UploadApiException: if information could not be obtained
        """
        url_safe_filename = urlparse.quote(filename)
        path = "/area/{uuid}/{filename}/validate".format(uuid=area_uuid, filename=url_safe_filename)
        response = self._make_request('get', path=path)
        return response.json()

    def validation_statuses(self, area_uuid):
        """
        Get count of validation statuses for all files in upload_area

        :param str area_uuid: A RFC4122-compliant ID for the upload area
        :return: a dict with key for each state and value being the count of files in that state
        :rtype: dict
        :raises UploadApiException: if information could not be obtained
        """
        path = "/area/{uuid}/validations".format(uuid=area_uuid)
        result = self._make_request('get', path)
        return result.json()

    def _make_request(self, verb, path, **kwargs):
        url = self._url(path)
        func = getattr(requests, verb)
        response = func(url=url, **kwargs)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise UploadApiException(
                "{method} returned {requests_exception}, content returned={content}".format(
                    method=response.request.method,
                    requests_exception=str(e),
                    content=response.content))
        else:
            return response

    def _url(self, path):
        if self.deployment_stage == 'prod':
            return "{base}{path}".format(base=UploadConfig().production_api_url, path=path)
        else:
            return "{base}{path}".format(
                base=UploadConfig().preprod_api_url_template.format(deployment_stage=self.deployment_stage),
                path=path)
