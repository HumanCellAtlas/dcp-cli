#!/usr/bin/env python
# coding: utf-8

import unittest, os, sys, filecmp, uuid, tempfile

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import hca.dss
from hca.util.compat import USING_PYTHON2
from test import reset_tweak_changes

if USING_PYTHON2:
    import backports.tempfile
    TemporaryDirectory = backports.tempfile.TemporaryDirectory
else:
    TemporaryDirectory = tempfile.TemporaryDirectory

class TestDssApi(unittest.TestCase):
    staging_bucket = "org-humancellatlas-dss-cli-test"

    def test_python_upload_download(self):
        with TemporaryDirectory() as dest_dir:
            dirpath = os.path.dirname(os.path.realpath(__file__))
            bundle_path = os.path.join(dirpath, "bundle")

            client = hca.dss.DSSClient()

            bundle_output = client.upload(src_dir=bundle_path, replica="aws", staging_bucket=self.staging_bucket)

            client.download(bundle_uuid=bundle_output['bundle_uuid'], dest_name=dest_dir, replica="aws")

            # Check that contents are the same
            for file in os.listdir(bundle_path):
                uploaded_file = os.path.join(bundle_path, file)
                downloaded_file = os.path.join(dest_dir, file)
                self.assertTrue(filecmp.cmp(uploaded_file, downloaded_file, False))

    def test_python_upload_lg_file(self):
        with TemporaryDirectory() as src_dir, TemporaryDirectory() as dest_dir:
            with tempfile.NamedTemporaryFile(dir=src_dir, suffix=".bin") as fh:
                fh.write(os.urandom(64 * 1024 * 1024 + 1))
                fh.flush()

                client = hca.dss.DSSClient()
                bundle_output = client.upload(src_dir=src_dir, replica="aws", staging_bucket=self.staging_bucket)

                client.download(bundle_output['bundle_uuid'], replica="aws", dest_name=dest_dir)

                downloaded_file = os.path.join(dest_dir, os.path.basename(fh.name))
                self.assertTrue(filecmp.cmp(fh.name, downloaded_file, False))

    def test_python_bindings(self):
        bundle_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "bundle")

        client = hca.dss.DSSClient()
        bundle_output = client.upload(src_dir=bundle_path, replica="aws", staging_bucket=self.staging_bucket)
        bundle_uuid = bundle_output['bundle_uuid']

        with TemporaryDirectory() as dest_dir:
            client.download(bundle_uuid=bundle_output['bundle_uuid'], replica="aws", dest_name=dest_dir)

        # Test get-files and head-files
        file_ = bundle_output['files'][0]
        with client.get_file.stream(uuid=file_['uuid'], replica="aws") as fh:
            while True:
                chunk = fh.raw.read(1024)
                if chunk == b"":
                    break
        self.assertTrue(client.head_file(uuid=file_['uuid'], replica="aws").ok)

        # Test get-bundles
        res = client.get_bundle(uuid=bundle_uuid, replica="aws")
        self.assertEqual(res["bundle"]["uuid"], bundle_uuid)

        # Test put-files
        file_uuid = str(uuid.uuid4())
        bundle_uuid = str(uuid.uuid4())
        source_url = "s3://{}/{}/{}".format(self.staging_bucket, file_['uuid'], file_['name'])
        client.put_file(uuid=file_uuid, creator_uid=1, bundle_uuid=bundle_uuid, source_url=source_url)

        # Test put-bundles
        files = [{'indexed': True,
                  'name': file_['name'],
                  'uuid': file_['uuid'],
                  'version': file_['version']}]
        res = client.put_bundle(uuid=bundle_uuid, files=files, creator_uid=1, replica="aws")
        self.assertTrue(len(res["version"]) > 0)

        with self.assertRaisesRegexp(Exception, "Missing query parameter 'replica'"):
            res = client.put_bundle(uuid=bundle_uuid, files=[], creator_uid=1)

    def test_python_subscriptions(self):
        client = hca.dss.DSSClient()

        query = {'bool': {}}
        resp = client.put_subscription(es_query=query, callback_url="www.example.com", replica="aws")
        subscription_uuid = resp['uuid']

        resp = client.get_subscriptions(replica="aws")
        self.assertTrue(subscription_uuid in [s['uuid'] for s in resp['subscriptions']])

        # GET /subscriptions does not support pagination
        with self.assertRaises(AttributeError):
            client.get_subscriptions.iterate(replica="aws")

        resp = client.get_subscription(replica="aws", uuid=subscription_uuid)
        self.assertEqual(subscription_uuid, resp['uuid'])

        resp = client.delete_subscription(uuid=subscription_uuid, replica="aws")
        self.assertIn('timeDeleted', resp)

        with self.assertRaisesRegexp(Exception, "Cannot find subscription!"):
            resp = client.get_subscription(replica="aws", uuid=subscription_uuid)

    def test_search(self):
        client = hca.dss.DSSClient()

        query = {}

        for result in client.post_search.iterate(es_query=query, replica="aws"):
            self.assertIn("bundle_fqid", result)

    @reset_tweak_changes
    def test_python_login_logout(self):
        client = hca.dss.DSSClient()
        query = {'bool': {}}
        resp = client.put_subscription(es_query=query, callback_url="www.example.com", replica="aws")
        self.assertIn("uuid", resp)

        access_token = "test_access_token"

        client.login(access_token=access_token)
        config = hca.get_config()

        self.assertEqual(config.oauth2_token.access_token, access_token)

        client.logout()

        self.assertNotIn("oauth2_token", config)


if __name__ == '__main__':
    unittest.main()
