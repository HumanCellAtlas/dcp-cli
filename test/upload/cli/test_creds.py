import os
import sys
from argparse import Namespace

import responses
import six

from ... import CapturingIO
from .. import UploadTestCase

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from hca.upload.cli.creds_command import CredsCommand


class TestUploadCliCredsCommand(UploadTestCase):

    @responses.activate
    def test_creds(self):
        area = self.mock_current_upload_area()
        self.simulate_credentials_api(area_uuid=area.uuid)

        with CapturingIO('stdout') as stdout:
            args = Namespace(uuid_or_alias=area.uuid)
            CredsCommand(args)

        six.assertRegex(self, stdout.captured(), "AWS_ACCESS_KEY_ID=")
        six.assertRegex(self, stdout.captured(), "AWS_SECRET_ACCESS_KEY=")
        six.assertRegex(self, stdout.captured(), "AWS_SESSION_TOKEN=")
