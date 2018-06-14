import os
import sys
import uuid

from .. import UploadTestCase

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import hca
from hca import upload
from hca.upload.exceptions import UploadException


class TestUploadSelectArea(UploadTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.area_uuid = str(uuid.uuid4())
        self.uri = "s3://org-humancellatlas-upload-test/{}/".format(self.area_uuid)

    def test_when_given_neither_a_uuid_or_uri_it_raises(self):

        with self.assertRaises(UploadException):
            upload.select_area()

    def test_when_given_an_unrecognized_uri_it_stores_it_in_upload_area_list_and_sets_it_as_current_area(self):
        upload.select_area(uri=self.uri)

        config = hca.get_config()
        self.assertIn(self.area_uuid, config.upload.areas)
        self.assertEqual(self.uri, config.upload.areas[self.area_uuid]['uri'])
        self.assertEqual(self.area_uuid, config.upload.current_area)

    def test_when_given_a_uuid_of_an_existing_area_it_selects_that_area(self):
        a_uuid = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
        b_uuid = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'
        config = hca.get_config()
        config.upload = {
            'areas': {
                a_uuid: {'uri': "s3://foo/{}/".format(a_uuid)},
                b_uuid: {'uri': "s3://foo/{}/".format(b_uuid)},
            },
        }
        config.save()

        upload.select_area(uuid=b_uuid)

        config = hca.get_config()
        self.assertEqual(b_uuid, config.upload.current_area)

    def test_when_given_a_uuid_of_an_unknown_area_it_raises_an_error(self):

        with self.assertRaises(UploadException):
            upload.select_area(uuid='bogobogo-bogo-bogo-bogo-areaaaaaaaaa')
