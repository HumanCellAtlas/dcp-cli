import os
import sys

import responses

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from hca import upload
from .. import UploadTestCase


class TestUploadFileUpload(UploadTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.area = self.mock_current_upload_area()

    @responses.activate
    def test_file_upload(self):
        self.simulate_credentials_api(area_uuid=self.area.uuid)

        file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'bundle', 'assay.json')
        upload.upload_file(file_path)

        obj = self.upload_bucket.Object("{}/assay.json".format(self.area.uuid))
        self.assertEqual(obj.content_type, 'application/json; dcp-type=data')
        with open(file_path, 'rb') as fh:
            expected_contents = fh.read()
            self.assertEqual(obj.get()['Body'].read(), expected_contents)

    @responses.activate
    def test_file_upload_with_target_filename_option(self):
        self.simulate_credentials_api(area_uuid=self.area.uuid)

        upload.upload_file('LICENSE', target_filename='POO')

        obj = self.upload_bucket.Object("{}/POO".format(self.area.uuid))
        self.assertEqual(obj.content_type, 'application/octet-stream; dcp-type=data')
        with open('LICENSE', 'rb') as fh:
            expected_contents = fh.read()
            self.assertEqual(obj.get()['Body'].read(), expected_contents)
