import os
import sys

from .. import UploadTestCase

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import hca
from hca import upload


class TestUploadListAreas(UploadTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()

    def test_list_areas_lists_areas_when_there_are_some(self):
        a_uuid = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
        b_uuid = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'
        config = hca.get_config()
        config.upload = {
            'areas': {
                a_uuid: {'uri': "s3://foo/{}/".format(a_uuid)},
                b_uuid: {'uri': "s3://foo/{}/".format(b_uuid)},
            },
            'current_area': a_uuid
        }
        config.save()

        areas = upload.list_areas()

        sorted_areas = sorted(areas, key=lambda k: k['uuid'])
        self.assertEqual(sorted_areas, [
            {'uuid': a_uuid, 'is_selected': True},
            {'uuid': b_uuid, 'is_selected': False}
        ])

    def test_list_areas_doesnt_error_when_the_upload_tweak_config_is_not_setup(self):
        config = hca.get_config()
        if 'upload' in config:
            del config['upload']
        try:
            hca.upload.list_areas()
        except Exception as e:
            self.fail("Expected no exception, got %s" % (e,))
