import os
import sys
import unittest
import uuid

import tweak

from ... import reset_tweak_changes

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import hca
from hca import upload
from hca.upload.exceptions import UploadException


class TestUploadSelectArea(unittest.TestCase):

    def setUp(self):
        self.area_uuid = str(uuid.uuid4())
        creds = "foo"
        self.urn = "dcp:upl:aws:dev:{}:{}".format(self.area_uuid, creds)

    @reset_tweak_changes
    def test_when_given_neither_a_uuid_or_urn_it_raises(self):

        with self.assertRaises(UploadException):
            upload.select_area()

    @reset_tweak_changes
    def test_when_given_an_unrecognized_urn_it_stores_it_in_upload_area_list_and_sets_it_as_current_area(self):
        upload.select_area(urn=self.urn)

        config = tweak.Config(hca.TWEAK_PROJECT_NAME)
        self.assertIn(self.area_uuid, config.upload.areas)
        self.assertEqual(self.urn, config.upload.areas[self.area_uuid])
        self.assertEqual(self.area_uuid, config.upload.current_area)

    @reset_tweak_changes
    def test_when_given_a_uuid_of_an_existing_area_it_selects_that_area(self):
        a_uuid = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
        b_uuid = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'
        config = tweak.Config(hca.TWEAK_PROJECT_NAME)
        config.upload = {
            'areas': {
                a_uuid: "dcp:upl:aws:dev:%s" % (a_uuid,),
                b_uuid: "dcp:upl:aws:dev:%s" % (b_uuid,),
            }
        }
        config.save()

        upload.select_area(uuid=b_uuid)

        config = tweak.Config(hca.TWEAK_PROJECT_NAME)
        self.assertEqual(b_uuid, config.upload.current_area)

    @reset_tweak_changes
    def test_when_given_a_uuid_of_an_unknown_area_it_raises_an_error(self):

        with self.assertRaises(UploadException):
            upload.select_area(uuid='bogobogo-bogo-bogo-bogo-areaaaaaaaaa')
