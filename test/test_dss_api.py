#!/usr/bin/env python
# coding: utf-8

import unittest, os, sys, filecmp, shutil, tempfile, uuid

import requests

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import hca.dss
from . import reset_tweak_changes


class TestDssApi(unittest.TestCase):

    def test_python_upload_download(self):
        dirpath = os.path.dirname(os.path.realpath(__file__))
        bundle_path = os.path.join(dirpath, "bundle")

        namespace = {'file_or_dir': [bundle_path],
                     'replica': "aws",
                     'staging_bucket': "org-humancellatlas-dss-cli-test"}

        bundle_output = hca.dss.upload(**namespace)

        downloaded_path = os.path.join(dirpath, "TestDownload")
        hca.dss.download(bundle_output['bundle_uuid'], name=downloaded_path)
        for file_info in hca.dss.Download._download_bundle(dict(
                uuid=bundle_output['bundle_uuid'],
                replica="aws"))[0]:
            self.assertNotEqual(file_info['content-type'], "binary/octet-stream")

        # Check that contents are the same
        for file in os.listdir(bundle_path):
            uploaded_file = os.path.join(bundle_path, file)
            downloaded_file = os.path.join(downloaded_path, file)
            self.assertTrue(filecmp.cmp(uploaded_file, downloaded_file, False))

        if os.path.exists(downloaded_path):
            shutil.rmtree(downloaded_path)

    def test_python_upload_lg_file(self):
        with tempfile.NamedTemporaryFile(suffix=".bin") as fh:
            fh.write(os.urandom(64 * 1024 * 1024 + 1))
            fh.flush()

            namespace = {'file_or_dir': [fh.name],
                         'replica': "aws",
                         'staging_bucket': "org-humancellatlas-dss-cli-test"}

            bundle_output = hca.dss.upload(**namespace)

            tempdir = tempfile.mkdtemp()
            try:
                hca.dss.download(bundle_output['bundle_uuid'], name=tempdir)

                downloaded_file = os.path.join(tempdir, os.path.basename(fh.name))
                self.assertTrue(filecmp.cmp(fh.name, downloaded_file, False))
            finally:
                if os.path.exists(tempdir):
                    shutil.rmtree(tempdir)

    def test_python_bindings(self):
        dirpath = os.path.dirname(os.path.realpath(__file__))
        bundle_path = os.path.join(dirpath, "bundle")
        staging_bucket = "org-humancellatlas-dss-cli-test"
        namespace = {'file_or_dir': [bundle_path],
                     'replica': "aws",
                     'staging_bucket': "org-humancellatlas-dss-cli-test"}

        bundle_output = hca.dss.upload(**namespace)

        hca.dss.download(bundle_output['bundle_uuid'], name=os.path.join(dirpath, "TestDownload"))

        # Test get-files and head-files
        file_ = bundle_output['files'][0]
        self.assertTrue(hca.dss.get_files(file_['uuid'], replica="aws").ok)
        self.assertTrue(hca.dss.head_files(file_['uuid'], replica="aws").ok)

        # Test get-bundles
        bundle_uuid = bundle_output['bundle_uuid']
        self.assertTrue(hca.dss.get_bundles(bundle_uuid, replica="aws").ok)

        # Test put-files
        file_uuid = str(uuid.uuid4())
        bundle_uuid = str(uuid.uuid4())
        source_url = "s3://{}/{}/{}".format(staging_bucket, file_['uuid'], file_['name'])
        self.assertTrue(hca.dss.put_files(file_uuid, creator_uid=1, bundle_uuid=bundle_uuid, source_url=source_url).ok)

        # Test put-bundles
        files = [{'indexed': True,
                  'name': file_['name'],
                  'uuid': file_['uuid'],
                  'version': file_['version']}]
        resp = hca.dss.put_bundles(bundle_uuid, files=files, creator_uid=1, replica="aws")
        self.assertTrue(resp.ok)

    def test_python_api_url(self):
        kwargs = {'uuid': "fake_uuid",
                  'replica': "aws",
                  'api_url': "https://thisisafakeurljslfjlshsfs.com"}
        self.assertRaises(requests.exceptions.ConnectionError,
                          hca.dss.get_files,
                          **kwargs)

    def test_python_subscriptions(self):
        query = {'bool': {}}
        resp = hca.dss.put_subscriptions(es_query=query, callback_url="www.example.com", replica="aws")
        subscription_uuid = resp.json()['uuid']

        self.assertEqual(201, resp.status_code)
        self.assertIn('uuid', resp.json())

        resp = hca.dss.get_subscriptions("aws")
        self.assertEqual(200, resp.status_code)
        self.assertTrue(subscription_uuid in [s['uuid'] for s in resp.json()['subscriptions']])

        resp = hca.dss.get_subscriptions(replica="aws", uuid=subscription_uuid)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(subscription_uuid, resp.json()['uuid'])

        resp = hca.dss.delete_subscriptions(uuid=subscription_uuid, replica="aws")
        self.assertEqual(200, resp.status_code)
        self.assertIn('timeDeleted', resp.json())

        resp = hca.dss.get_subscriptions("aws", uuid=subscription_uuid)
        self.assertEqual(404, resp.status_code)

    @reset_tweak_changes
    def test_python_login(self):
        from tweak import Config

        access_token = "test_access_token"
        out = {'completed': True}

        login = hca.dss.login(access_token=access_token)
        config = Config(hca.TWEAK_PROJECT_NAME)

        self.assertEqual(login, out)
        self.assertEqual(config.login.access_token, access_token)


if __name__ == '__main__':
    unittest.main()
