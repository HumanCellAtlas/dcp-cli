#!/usr/bin/env python
# coding: utf-8
import errno
from concurrent.futures import ThreadPoolExecutor
import datetime
import filecmp
from hca.util import tsv
import itertools
import os
import sys
import tempfile
import uuid
import unittest
from fnmatch import fnmatchcase

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import hca.dss
from hca.dss.util import iter_paths, object_name_builder
from test import reset_tweak_changes, TEST_DIR


class TestDssApi(unittest.TestCase):
    staging_bucket = "org-humancellatlas-dss-cli-test"

    @classmethod
    def setUpClass(cls):
        cls.client = hca.dss.DSSClient()

    def test_set_host(self):
        with tempfile.TemporaryDirectory() as home:
            with unittest.mock.patch.dict(os.environ, HOME=home):
                dev = hca.dss.DSSClient(
                    swagger_url="https://dss.dev.data.humancellatlas.org/v1/swagger.json")
                self.assertEqual("dss.dev.data.humancellatlas.org", dev._swagger_spec['host'])

    def test_set_host_multithreaded(self):
        num_repeats = 10
        num_threads = 2
        for repeat in range(num_repeats):
            with self.subTest(repeat=repeat):
                with tempfile.TemporaryDirectory() as config_dir:
                    with unittest.mock.patch.dict(os.environ, XDG_CONFIG_HOME=config_dir):

                        def f(_):
                            dev = hca.dss.DSSClient(
                                swagger_url="https://dss.dev.data.humancellatlas.org/v1/swagger.json")
                            self.assertEqual('dss.dev.data.humancellatlas.org', dev._swagger_spec['host'])

                        with ThreadPoolExecutor(num_threads) as tpe:
                            self.assertTrue(all(x is None for x in tpe.map(f, range(num_threads))))

    @unittest.skipIf(os.name is 'nt', 'Unable to test on Windows')  # TODO windows testing refactor
    def test_python_nested_bundle_upload_download(self):
        bundle_path = os.path.join(TEST_DIR, "upload", "data")
        uploaded_paths = [x.path for x in iter_paths(str(bundle_path))]
        uploaded_files = [object_name_builder(p, bundle_path) for p in uploaded_paths]
        client = hca.dss.DSSClient(swagger_url="https://dss.dev.data.humancellatlas.org/v1/swagger.json")

        manifest = client.upload(src_dir=bundle_path,
                                 replica="aws",
                                 staging_bucket=self.staging_bucket)
        manifest_files = manifest['files']
        self.assertEqual(list(file['name'] for file in manifest_files).sort(), uploaded_files.sort())
        bundle_uuid = manifest['bundle_uuid']
        with self.subTest(bundle_uuid=bundle_uuid):
            with tempfile.TemporaryDirectory() as dest_dir:
                client.download(bundle_uuid=bundle_uuid, replica='aws', download_dir=dest_dir)
                downloaded_file_names = [x.path for x in iter_paths(dest_dir)]
                downloaded_file_paths = [object_name_builder(p, dest_dir) for p in downloaded_file_names]
                self.assertEqual(uploaded_files.sort(), downloaded_file_paths.sort())

    def test_python_upload_download(self):
        bundle_path = os.path.join(TEST_DIR, "res", "bundle")
        uploaded_files = set(os.listdir(bundle_path))

        manifest = self.client.upload(src_dir=bundle_path,
                                      replica="aws",
                                      staging_bucket=self.staging_bucket)
        manifest_files = manifest['files']
        bundle_fqid = manifest['bundle_uuid'] + '.' + manifest['version']
        self.assertEqual({file['name'] for file in manifest_files}, uploaded_files)

        # Work around https://github.com/HumanCellAtlas/data-store/issues/1331
        for file in manifest_files:
            file['indexed'] = file['name'].endswith('.json')

        for metadata_globs in (), ('',), ('*',), ('a[s][s]ay.json',):
            for data_globs in (), ('',), ('*',), ('*_1.fastq.gz',):
                with self.subTest(metadata_files=metadata_globs, data_files=data_globs):
                    bundle_uuid = manifest['bundle_uuid']
                    expect_downloaded_files = {
                        file['name'] for file in manifest_files
                        if any(fnmatchcase(file['name'], glob)
                               for glob in (metadata_globs if file['indexed'] else data_globs))}

                    if '*' in metadata_globs and '*' in data_globs:
                        # In the test case where we download all files, add another wrinkle to the test: Upload a new
                        # version of one of the metadata files. That new file version is not referenced by any
                        # bundle. The subsequent download should not be affected by that new version since the bundle
                        # still refers to the old version.
                        file1, file2 = itertools.islice((f for f in manifest_files if f['name'].endswith('.json')), 2)
                        file_version = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H%M%S.%fZ")
                        source_url = "s3://{}/{}/{}".format(self.staging_bucket, file2['uuid'], file2['name'])
                        self.client.put_file(uuid=file1['uuid'],
                                             version=file_version,
                                             creator_uid=1,
                                             bundle_uuid=bundle_uuid,
                                             source_url=source_url)

                    with tempfile.TemporaryDirectory() as dest_dir:
                        self.client.download(bundle_uuid=bundle_uuid,
                                             download_dir=dest_dir,
                                             replica="aws",
                                             data_filter=data_globs,
                                             metadata_filter=metadata_globs)
                        # Check that contents are the same
                        try:
                            downloaded_files = set(os.listdir(os.path.join(dest_dir, bundle_fqid)))
                        except OSError as e:
                            if e.errno != errno.ENOENT:
                                raise
                            downloaded_files = set()
                        if '.hca' in downloaded_files:
                            # Since we set the download_dir for download, .hca dir will appear,
                            # but only if globs are non-empty
                            assert not all(glob in [(), ('',)] for glob in [metadata_globs, data_globs])
                            downloaded_files.remove('.hca')
                        downloaded_files.remove('bundle.json')
                        self.assertEqual(expect_downloaded_files, downloaded_files)
                        for file in downloaded_files:
                            manifest_entry = next(entry for entry in manifest['files'] if entry['name'] == file)
                            globs = metadata_globs if manifest_entry['indexed'] else data_globs
                            self.assertTrue(any(fnmatchcase(file, glob) for glob in globs))
                            uploaded_file = os.path.join(bundle_path, file)
                            downloaded_file = os.path.join(dest_dir, bundle_fqid, file)
                            self.assertTrue(filecmp.cmp(uploaded_file, downloaded_file, False))

    def test_python_manifest_download(self):
        bundle_path = os.path.join(TEST_DIR, "res", "bundle")
        uploaded_files = set(os.listdir(bundle_path))

        manifest = self.client.upload(src_dir=bundle_path,
                                      replica="aws",
                                      staging_bucket=self.staging_bucket)
        manifest_files = manifest['files']
        self.assertEqual({file['name'] for file in manifest_files}, uploaded_files)

        # Work around https://github.com/HumanCellAtlas/data-store/issues/1331
        for file in manifest_files:
            file['indexed'] = file['name'].endswith('.json')

        bundle_uuid = manifest['bundle_uuid']
        bundle_version = manifest['version']
        bundle_fqid = bundle_uuid + '.' + bundle_version
        data_files = tuple(file['name'] for file in manifest_files if not file['indexed'])

        for bad_bundle in False, True:
            with self.subTest(bad_bundle=bad_bundle):
                with tempfile.TemporaryDirectory() as work_dir:
                    cwd = os.getcwd()
                    os.chdir(work_dir)
                    try:
                        with open('manifest.tsv', 'w', newline='') as manifest:
                            writer = tsv.DictWriter(manifest,
                                                    fieldnames=('bundle_uuid',
                                                                'bundle_version',
                                                                'file_name',
                                                                'file_sha256'))
                            writer.writeheader()
                            writer.writerow(dict(bundle_uuid=bundle_uuid,
                                                 bundle_version=bundle_version,
                                                 file_name=data_files[0],
                                                 file_sha256=
                                                 '9b4c0dde8683f924975d0867903dc7a9'
                                                 '67f46bee5c0a025c451b9ba73e43f120'))
                            if bad_bundle:
                                writer.writerow(dict(bundle_uuid=str(uuid.uuid4()),
                                                     bundle_version=bundle_version,
                                                     file_name=data_files[0],
                                                     file_sha256=
                                                     '9b4c0dde8683f924975d0867903dc7a9'
                                                     '67f46bee5c0a025c451b9ba73e43f120'))

                        dest_dir = os.path.join(work_dir, bundle_fqid)
                        try:
                            self.client.download_manifest('manifest.tsv', replica="aws", layout='bundle')
                        except RuntimeError as e:
                            self.assertTrue(bad_bundle, "Should only raise with a bad bundle in the manifest")
                            self.assertEqual('1 download task(s) failed.', e.args[0])
                        else:
                            self.assertFalse(bad_bundle)
                        for file in manifest_files:
                            uploaded_file = os.path.join(bundle_path, file['name'])
                            downloaded_file = os.path.join(dest_dir, file['name'])
                            if file['indexed'] or file['name'] == data_files[0]:
                                self.assertTrue(filecmp.cmp(uploaded_file, downloaded_file, False))
                            else:
                                self.assertTrue(os.path.exists(uploaded_file))
                                self.assertFalse(os.path.exists(downloaded_file))
                    finally:
                        os.chdir(cwd)

    @unittest.skipIf(os.name is 'nt', 'Unable to test on Windows')  # TODO windows testing refactor
    def test_python_upload_lg_file(self):
        with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as dest_dir:
            with tempfile.NamedTemporaryFile(dir=src_dir, suffix=".bin") as fh:
                fh.write(os.urandom(64 * 1024 * 1024 + 1))
                fh.flush()

                client = hca.dss.DSSClient()
                bundle_output = client.upload(src_dir=src_dir, replica="aws", staging_bucket=self.staging_bucket)

                client.download(bundle_output['bundle_uuid'], replica="aws", download_dir=dest_dir)

                bundle_fqid = bundle_output['bundle_uuid'] + '.' + bundle_output['version']
                downloaded_file = os.path.join(dest_dir, bundle_fqid, os.path.basename(fh.name))
                self.assertTrue(filecmp.cmp(fh.name, downloaded_file, False))

    def test_python_bindings(self):
        bundle_path = os.path.join(TEST_DIR, "res", "bundle")
        bundle_output = self.client.upload(src_dir=bundle_path, replica="aws", staging_bucket=self.staging_bucket)
        bundle_uuid = bundle_output['bundle_uuid']

        with tempfile.TemporaryDirectory() as dest_dir:
            self.client.download(bundle_uuid=bundle_output['bundle_uuid'], replica="aws", download_dir=dest_dir)

        # Test get-files and head-files
        file_ = bundle_output['files'][0]
        with self.client.get_file.stream(uuid=file_['uuid'], replica="aws") as fh:
            while True:
                chunk = fh.raw.read(1024)
                if chunk == b"":
                    break
        self.assertTrue(self.client.head_file(uuid=file_['uuid'], replica="aws").ok)

        # Test get-bundles
        res = self.client.get_bundle(uuid=bundle_uuid, replica="aws")
        self.assertEqual(res["bundle"]["uuid"], bundle_uuid)

        # Test put-files
        file_uuid = str(uuid.uuid4())
        file_version = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H%M%S.%fZ")
        bundle_uuid = str(uuid.uuid4())
        source_url = "s3://{}/{}/{}".format(self.staging_bucket, file_['uuid'], file_['name'])
        res = self.client.put_file(uuid=file_uuid, creator_uid=1, bundle_uuid=bundle_uuid,
                                   version=file_version, source_url=source_url)

        # Test put-bundles
        files = [{'indexed': True,
                  'name': file_['name'],
                  'uuid': file_uuid,
                  'version': res['version']}]
        res = self.client.put_bundle(uuid=bundle_uuid, files=files, version=file_version, creator_uid=1, replica="aws")
        self.assertEqual(res["version"], file_version)

        with self.assertRaisesRegexp(Exception, "Missing query parameter 'replica'"):
            res = self.client.put_bundle(uuid=bundle_uuid, files=[], version=file_version, creator_uid=1)

    def test_python_subscriptions(self):
        query = {'bool': {}}
        resp = self.client.put_subscription(es_query=query,
                                            callback_url="https://www.test_python_subscriptions.dss.hca.org",
                                            replica="aws")
        subscription_uuid = resp['uuid']

        resp = self.client.get_subscriptions(replica="aws", subscription_type='elasticsearch')
        self.assertTrue(subscription_uuid in [s['uuid'] for s in resp['subscriptions']],
                        str(subscription_uuid) + ' not found in:\n' + str(resp))

        # GET /subscriptions does not support pagination
        with self.assertRaises(AttributeError):
            self.client.get_subscriptions.iterate(replica="aws", subscription_type='elasticsearch')

        resp = self.client.get_subscription(replica="aws", uuid=subscription_uuid, subscription_type='elasticsearch')
        self.assertEqual(subscription_uuid, resp['uuid'])

        resp = self.client.delete_subscription(uuid=subscription_uuid, replica="aws", subscription_type='elasticsearch')
        self.assertIn('timeDeleted', resp)

        with self.assertRaisesRegexp(Exception, "Cannot find subscription!"):
            resp = self.client.get_subscription(replica="aws", uuid=subscription_uuid, subscription_type='elasticsearch')

        # Test subscriptions version 2 (jmespath subscriptions)
        resp = self.client.put_subscription(callback_url="https://www.test_python_subscriptions.dss.hca.org",
                                            replica="aws")
        subscription_uuid = resp['uuid']

        resp = self.client.get_subscriptions(replica="aws", subscription_type="jmespath")
        self.assertTrue(subscription_uuid in [s['uuid'] for s in resp['subscriptions']])

        # GET /subscriptions does not support pagination
        with self.assertRaises(AttributeError):
            self.client.get_subscriptions.iterate(replica="aws", subscription_type="jmespath")

        resp = self.client.get_subscription(replica="aws", subscription_type="jmespath", uuid=subscription_uuid)
        self.assertEqual(subscription_uuid, resp['uuid'])

        resp = self.client.delete_subscription(uuid=subscription_uuid, subscription_type="jmespath", replica="aws")
        self.assertIn('timeDeleted', resp)

        with self.assertRaisesRegexp(Exception, "Cannot find subscription!"):
            resp = self.client.get_subscription(replica="aws", subscription_type="jmespath", uuid=subscription_uuid)

    def test_search_iteration_pagination(self, limit=128):
        query = {}

        with self.subTest('Test POST search iteration() method.'):
            for ix, result in enumerate(self.client.post_search.iterate(es_query=query, replica="aws")):
                self.assertIn("bundle_fqid", result)
                if ix > limit:
                    break

        with self.subTest('Test POST search pagination() method.'):
            for ix, result in enumerate(self.client.post_search.paginate(es_query=query, replica="aws")):
                self.assertIn("es_query", result)
                self.assertIn("results", result)
                self.assertIn("total_hits", result)
                if ix > limit:
                    break

    def test_collections_iteration_pagination(self, limit=128):
        with self.subTest('Test GET collections iteration() method.'):
            for ix, result in enumerate(self.client.get_collections.iterate()):
                self.assertIn("uuid", result)
                self.assertIn("version", result)
                if ix > limit:
                    break

        with self.subTest('Test GET collections pagination() method.'):
            for ix, result in enumerate(self.client.get_collections.paginate()):
                self.assertIn("collections", result)
                if ix > limit:
                    break

    def test_get_bundle_iteration_pagination(self, limit=128):
        bundle_path = os.path.join(TEST_DIR, "res", "bundle")
        bundle_output = self.client.upload(src_dir=bundle_path, replica="aws", staging_bucket=self.staging_bucket)
        bundle_uuid = bundle_output['bundle_uuid']

        with self.subTest('Test GET bundle iterate() method.'):
            for ix, result in enumerate(self.client.get_bundle.iterate(uuid=bundle_uuid, replica="aws")):
                self.assertIn("name", result)
                self.assertIn("content-type", result)
                self.assertIn("indexed", result)
                self.assertIn("uuid", result)
                self.assertIn("version", result)
                self.assertIn("size", result)
                self.assertIn("crc32c", result)
                self.assertIn("s3_etag", result)
                self.assertIn("sha1", result)
                self.assertIn("sha256", result)
                if ix > limit:
                    break

        with self.subTest('Test GET bundle paginate() method.'):
            for ix, result in enumerate(self.client.get_bundle.paginate(uuid=bundle_uuid, replica="aws")):
                self.assertIn("bundle", result)
                if ix > limit:
                    break

    def test_clear_cache(self):
        """Testing clear_cache by comparing the creation date of the old swagger with the refreshed swagger that
        replaces it"""
        client = hca.dss.DSSClient()
        swagger_filename = client._get_swagger_filename(client.swagger_url)
        self.assertTrue(os.path.isfile(swagger_filename), "Pass if file exists initially")
        old_swagger = datetime.datetime.fromtimestamp(os.path.getmtime(swagger_filename))
        client.clear_cache()
        new_swagger = datetime.datetime.fromtimestamp(os.path.getmtime(swagger_filename))
        self.assertGreater(new_swagger, old_swagger)


    @reset_tweak_changes
    def test_python_login_logout_service_account(self):
        query = {'bool': {}}
        resp = self.client.put_subscription(es_query=query,
                                            callback_url=
                                            "https://www.test_python_login_logout_service_account.dss.hca.org",
                                            replica="aws")
        self.assertIn("uuid", resp)

        deletion_resp = self.client.delete_subscription(uuid=resp['uuid'], replica='aws',
                                                        subscription_type='elasticsearch')
        self.assertIn("timeDeleted", deletion_resp)
        access_token = "test_access_token"

        self.client.login(access_token=access_token)
        config = hca.get_config()

        self.assertEqual(config.oauth2_token.access_token, access_token)
        self.client.logout()
        self.assertNotIn("oauth2_token", config)

    @unittest.skipIf(True, "Manual Test")
    @reset_tweak_changes
    def test_python_login_logout_user_account(self):
        config = hca.get_config()

        self.client.logout()
        self.assertNotIn("oauth2_token", config)
        self.assertNotIn("application_secrets", config)

        self.client.login()
        self.assertIn("oauth2_token", config)
        self.assertIn("application_secrets", config)

        query = {'bool': {}}
        resp = self.client.put_subscription(es_query=query,
                                            callback_url=
                                            "https://www.test_python_login_logout_service_account.dss.hca.org",
                                            replica="aws")
        self.assertIn("uuid", resp)
        self.client.delete_subscription(uuid=resp["uuid"], replica="aws", subscription_type='elasticsearch')

        self.client.logout()
        self.assertNotIn("oauth2_token", config)


if __name__ == "__main__":
    unittest.main()
