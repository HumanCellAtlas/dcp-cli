import os
import sys

import responses

from .. import UploadTestCase

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from hca import upload


class TestGetCredentials(UploadTestCase):

    def test_get_credentials(self):

        area = self.mock_current_upload_area()
        creds_url = self.simulate_credentials_api(area_uuid=area.uuid)

        upload.get_credentials(area.uuid)

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, creds_url)
