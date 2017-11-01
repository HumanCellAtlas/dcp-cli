import os
import sys
import unittest

from ... import reset_tweak_changes
from .. import mock_upload_area, mock_current_upload_area

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from hca.upload import UploadConfig, UploadException, forget_area


class TestUploadForget(unittest.TestCase):

    @reset_tweak_changes
    def test_when_given_an_alias_that_matches_one_area_it_forgets_that_area(self):
        area = mock_current_upload_area()
        self.assertIn(area.uuid, UploadConfig().areas())
        self.assertEqual(area.uuid, UploadConfig().current_area)

        forget_area(area.uuid)

        self.assertNotIn(area.uuid, UploadConfig().areas())
        self.assertEqual(None, UploadConfig().current_area)

    @reset_tweak_changes
    def test_when_given_an_alias_that_matches_no_areas_it_raises(self):

        with self.assertRaises(UploadException):
            forget_area('bogo-uuid')

    @reset_tweak_changes
    def test_when_given_an_alias_that_matches_more_than_one_area_it_raises(self):
        mock_upload_area('deadbeef-dead-dead-dead-beeeeeeeeeef')
        mock_upload_area('deafbeef-deaf-deaf-deaf-beeeeeeeeeef')

        with self.assertRaises(UploadException):
            forget_area('dea')
