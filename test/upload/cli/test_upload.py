import os
import sys
from argparse import Namespace
from mock import patch, Mock

import responses

from .. import UploadTestCase

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from hca.upload.cli.upload_command import UploadCommand


class TestUploadCliUploadCommand(UploadTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.area = self.mock_current_upload_area()

    @responses.activate
    def test_upload_with_target_filename_option(self):

        args = Namespace(
            file_paths=['test/bundle/sample.json'],
            target_filename='FOO',
            no_transfer_acceleration=False,
            quiet=True)

        self.simulate_credentials_api(area_uuid=self.area.uuid)

        UploadCommand(args)

        obj = self.upload_bucket.Object("{}/FOO".format(self.area.uuid))
        self.assertEqual(obj.content_type, 'application/json; dcp-type=data')
        with open('test/bundle/sample.json', 'rb') as fh:
            expected_contents = fh.read()
            self.assertEqual(obj.get()['Body'].read(), expected_contents)

    @responses.activate
    def test_upload_with_dcp_type_option(self):

        args = Namespace(file_paths=['LICENSE'], target_filename=None, no_transfer_acceleration=False, quiet=True)

        self.simulate_credentials_api(area_uuid=self.area.uuid)

        UploadCommand(args)

        obj = self.upload_bucket.Object("{}/LICENSE".format(self.area.uuid))
        self.assertEqual(obj.content_type, 'application/octet-stream; dcp-type=data')
        with open('LICENSE', 'rb') as fh:
            expected_contents = fh.read()
            self.assertEqual(obj.get()['Body'].read(), expected_contents)

    @responses.activate
    @patch('hca.upload.s3_agent.S3Agent.upload_file')   # Don't actually try to upload
    def test_no_transfer_acceleration_option_sets_up_botocore_config_correctly(self, upload_file_stub):
        import botocore

        with patch('hca.upload.s3_agent.Config', new=Mock(wraps=botocore.config.Config)) as mock_config:

            args = Namespace(file_paths=['LICENSE'], target_filename=None, quiet=True)
            args.no_transfer_acceleration = False

            self.simulate_credentials_api(area_uuid=self.area.uuid)

            UploadCommand(args)
            mock_config.assert_called_once_with(s3={'use_accelerate_endpoint': True})

            mock_config.reset_mock()
            args.no_transfer_acceleration = True
            UploadCommand(args)
            mock_config.assert_called_once_with()

    @responses.activate
    def test_multiple_uploads(self):

        files = ['LICENSE', 'README.rst']
        args = Namespace(file_paths=files, target_filename=None, no_transfer_acceleration=False,
                         dcp_type=None, quiet=True)

        self.simulate_credentials_api(area_uuid=self.area.uuid)

        UploadCommand(args)

        for filename in files:
            obj = self.upload_bucket.Object("{}/{}".format(self.area.uuid, filename))
            with open(filename, 'rb') as fh:
                expected_contents = fh.read()
                self.assertEqual(obj.get()['Body'].read(), expected_contents)
