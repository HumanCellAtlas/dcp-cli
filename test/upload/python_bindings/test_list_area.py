import os
import sys
import unittest

import requests_mock

from ... import reset_tweak_changes

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from hca import upload
from .. import mock_current_upload_area, mock_upload_area


class TestUploadListArea(unittest.TestCase):

    @reset_tweak_changes
    def test_list_current_area(self):
        area = mock_current_upload_area()

        with requests_mock.mock() as m:
            mock_url = 'https://upload.test.data.humancellatlas.org/v1/area/{uuid}'.format(uuid=area.uuid)
            m.get(mock_url, text='{"files":[{"some":"data"}]}')

            file_list = upload.list_current_area()

        self.assertEqual(file_list, [{'some': 'data'}])

    @reset_tweak_changes
    def test_list_area(self):
        area1 = mock_upload_area()
        area2 = mock_upload_area()

        with requests_mock.mock() as m:
            area1_mock_url = 'https://upload.test.data.humancellatlas.org/v1/area/{uuid}'.format(uuid=area1.uuid)
            area2_mock_url = 'https://upload.test.data.humancellatlas.org/v1/area/{uuid}'.format(uuid=area2.uuid)
            m.get(area1_mock_url, text='{"files":[{"area1":"file"}]}')
            m.get(area2_mock_url, text='{"files":[{"area2":"file"}]}')

            file_list = upload.list_area(area1.uuid)

        self.assertEqual(file_list, [{'area1': 'file'}])
