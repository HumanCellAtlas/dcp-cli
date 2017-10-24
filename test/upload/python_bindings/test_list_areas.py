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


class TestUploadListAreas(unittest.TestCase):

    def setUp(self):
        self.area_uuid = str(uuid.uuid4())
        creds = "foo"
        self.urn = "dcp:upl:aws:dev:{}:{}".format(self.area_uuid, creds)

    @reset_tweak_changes
    def test_list_areas_lists_areas_when_there_are_some(self):
        a_uuid = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
        b_uuid = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'
        config = tweak.Config(hca.TWEAK_PROJECT_NAME)
        config.upload = {
            'areas': {
                a_uuid: "dcp:upl:aws:dev:%s" % (a_uuid,),
                b_uuid: "dcp:upl:aws:dev:%s" % (b_uuid,),
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

    @reset_tweak_changes
    def test_list_areas_doesnt_error_when_the_upload_tweak_config_is_not_setup(self):
        config = tweak.Config(hca.TWEAK_PROJECT_NAME, autosave=True)
        if 'upload' in config:
            del config['upload']
        try:
            hca.upload.list_areas()
        except Exception as e:
            self.fail("Expected no exception, got %s" % (e,))
