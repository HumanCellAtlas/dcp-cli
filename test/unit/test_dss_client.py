import errno
import hashlib
import logging
import os
import random
import tempfile
import threading
import time
import unittest
import uuid

from mock import patch
from hca.util.compat import walk
from hca.dss import DSSClient, ManifestDownloadContext, TaskRunner
from test.unit import TmpDirTestCase

logging.basicConfig()


def _touch_file(path):
    try:
        os.makedirs(os.path.split(path)[0])
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    with open(path, 'w'):
        pass


def _fake_download_file(*args, **kwargs):
    _touch_file(args[1])


def _make_fake_paginate(fake_hash=False):
    def _fake_get_bundle_paginate(*args, **kwargs):
        bundle_dict = {
            'version': '1_version',
            'files': [
                {
                    'uuid': 'a_uuid',
                    'version': '1_version',
                    'name': 'a_file_name',
                    'indexed': False,
                    'sha256': 'ad3fc1e4898e0bce096be5151964a81929dbd2a92bd5ed56a39a8e133053831d',
                    'size': 12
                }, {
                    'uuid': 'b_uuid',
                    'version': '2_version',
                    'name': 'b_file_name',
                    'indexed': False,
                    'sha256': '8f35071eaeedd9d6f575a8b0f291daeac4c1dfdfa133b5c561232a00bf18c4b4',
                    'size': 4
                }, {
                    'uuid': 'c_uuid',
                    'version': '3_version',
                    'name': 'c_file_name',
                    'indexed': False,
                    'sha256': '8f3404db04bdede03e9128a4b48599d0ecde5b2e58ed9ce52ce84c3d54a3429c',
                    'size': 36
                }, {
                    'uuid': 'd_uuid',
                    'version': '4_version',
                    'name': 'metadata_file.pdf',
                    'indexed': True,
                    'sha256': '8ffe4838ac08672041f73f82e5f8361860627271ec31aa479fbb65f2ccc46d05',
                    'size': 9
                }
            ]
        }
        # This ensures that each bundle.json is distinct
        for f in bundle_dict['files']:
            f['bundle_uuid'] = kwargs['uuid']
            if fake_hash:
                f['sha256'] = 'fakehash'
        yield {'bundle': bundle_dict}
    return _fake_get_bundle_paginate


barrier = threading.Barrier(3)


def _fake_do_download_file_with_barrier(*args, **kwargs):
    """
    Wait for friends before trying to "download" the same fake file
    """
    barrier.wait()
    fh = args[1]
    fh.write(b'Here we write some stuff so that the fake download takes some time. '
             b'This helps ensure that multiple threads are writing at once and thus '
             b'allows us to test for race conditions.')
    time.sleep(random.random())
    return 'FAKEhash'


class DSSClientTestCase(TmpDirTestCase):
    maxDiff = None
    manifest = list(zip(
        ('bundle_uuid', 'a_uuid', 'b_uuid', 'c_uuid'),
        ('bundle_version', '1_version', '1_version', '1_version'),
        ('file_content_type', 'somestuff', 'somestuff', 'somestuff'),
        ('file_name', 'a_file_name', 'b_file_name', 'c_file_name'),
        ('file_sha256',
         'ad3fc1e4898e0bce096be5151964a81929dbd2a92bd5ed56a39a8e133053831d',
         '8F35071EAEEDD9D6F575A8B0F291DAEAC4C1DFDFA133B5C561232A00BF18C4B4',
         '8f3404db04bdede03e9128a4b48599d0ecde5b2e58ed9ce52ce84c3d54a3429c'),
        ('file_size', '12', '2', '41'),
        ('file_uuid', 'af_uuid', 'bf_uuid', 'cf_uuid'),
        ('file_version', 'af_version', 'af_version', 'af_version'),
        ('file_indexed', 'False', 'False', 'False'),
    ))
    version_dir = os.path.join('.hca', 'v2', 'files_2_4')

    def setUp(self):
        super().setUp()
        self.dss = DSSClient()
        self._write_manifest(self.manifest)
        self.manifest_file = 'manifest.tsv'

    def tearDown(self):
        super().tearDown()

    def _write_manifest(self, manifest):
        with open('manifest.tsv', 'w') as f:
            f.write('\n'.join(['\t'.join(row) for row in manifest]))

    def _write_uniform_manifest(self):
        """Create a manifest where all files have the same hash"""
        new_manifest = [self.manifest[0]]
        for row in self.manifest[1:]:
            new_row = list(row)
            new_row[4] = 'fakeHASH'
            new_manifest.append(new_row)
        self._write_manifest(new_manifest)

    def _files_present(self):
        return {os.path.join(dir_path, f)
                for dir_path, _, files in walk('.')
                for f in files}

    def _mock_download_manifest(self, *args, **kwargs):
        with patch('hca.dss.DownloadContext._download_file', side_effect=_fake_download_file) as download_func:
            with patch('hca.dss.DSSClient.get_bundle') as mock_get_bundle:
                mock_get_bundle.paginate = _make_fake_paginate()
                self.dss.download_manifest(*args, **kwargs)
        return download_func

    def _mock_download(self, *args, **kwargs):
        with patch('hca.dss.DownloadContext._download_file', side_effect=_fake_download_file):
            with patch('hca.dss.DSSClient.get_bundle') as mock_get_bundle:
                mock_get_bundle.paginate = _make_fake_paginate()
                self.dss.download(*args, **kwargs)

    def _assert_all_files_downloaded(self, more_files=None, prefix=''):
        prefix = os.path.join(prefix, self.version_dir)
        files_present = self._files_present()
        # Add dots so that files match what `walk()` returns
        if any([f.startswith('.') for f in files_present]):
            prefix = os.path.join('.', prefix)
        files_expected = {
            os.path.join('.', os.path.basename(self.manifest_file)),
            os.path.join(prefix, 'ad', '3fc1', 'ad3fc1e4898e0bce096be5151964a81929dbd2a92bd5ed56a39a8e133053831d'),
            os.path.join(prefix, '8f', '3507', '8f35071eaeedd9d6f575a8b0f291daeac4c1dfdfa133b5c561232a00bf18c4b4'),
            os.path.join(prefix, '8f', '3404', '8f3404db04bdede03e9128a4b48599d0ecde5b2e58ed9ce52ce84c3d54a3429c'),
        }
        if more_files:
            files_expected.update(more_files)
        self.assertEqual(files_expected, files_expected)

    def _assert_manifest_updated_with_paths(self, prefix):
        output_manifest = os.path.basename(self.manifest_file)
        self.assertTrue(os.path.isfile(output_manifest))
        with open(output_manifest, 'r') as f:
            output_manifest = [tuple(line.split('\t')) for line in f.read().splitlines()]
        expected_manifest = list(zip(*self.manifest))
        version_dir = os.path.join(prefix, '.hca', 'v2', 'files_2_4')
        expected_manifest.append((
            'file_path',
            os.path.join(version_dir, 'ad', '3fc1', 'ad3fc1e4898e0bce096be5151964a81929dbd2a92bd5ed56a39a8e133053831d'),
            os.path.join(version_dir, '8f', '3507', '8f35071eaeedd9d6f575a8b0f291daeac4c1dfdfa133b5c561232a00bf18c4b4'),
            os.path.join(version_dir, '8f', '3404', '8f3404db04bdede03e9128a4b48599d0ecde5b2e58ed9ce52ce84c3d54a3429c')
        ))
        expected_manifest = list(zip(*expected_manifest))
        self.assertEqual(output_manifest, expected_manifest)

    def _assert_manifest_not_updated(self):
        for row in ManifestDownloadContext._parse_manifest(self.manifest_file):
            self.assertNotIn('file_path', row)


class TestManifestDownloadFilestore(DSSClientTestCase):

    @patch('hca.dss.DownloadContext.DIRECTORY_NAME_LENGTHS', [1, 3, 2])
    def test_file_path(self):
        self.assertRaises(AssertionError, ManifestDownloadContext._file_path, 'a', '.')
        parts = ManifestDownloadContext._file_path('abcdefghij', '.').split(os.sep)
        self.assertEqual(parts, ['.', '.hca', 'v2', 'files_1_3_2', 'a', 'bcd', 'ef', 'abcdefghij'])

    @patch('hca.dss.DownloadContext.DIRECTORY_NAME_LENGTHS', [1, 3, 2])
    def test_file_path_filestore_root(self):
        self.assertRaises(AssertionError, ManifestDownloadContext._file_path, 'a', 'nested_filestore')
        parts = ManifestDownloadContext._file_path('abcdefghij', 'nested_filestore').split(os.sep)
        self.assertEqual(parts, ['nested_filestore', '.hca', 'v2', 'files_1_3_2', 'a', 'bcd', 'ef', 'abcdefghij'])

    @patch('logging.Logger.warning')
    def test_manifest_download(self, warning_log):
        download_func = self._mock_download_manifest(self.manifest_file, 'aws', layout='none')
        self.assertEqual(download_func.call_count, len(self.manifest) - 1)
        self.assertEqual(warning_log.call_count, 1, 'Only expected warning for overwriting manifest')
        # Since files now exist, running again ensures that we avoid unnecessary downloads
        self._mock_download_manifest(self.manifest_file, 'aws', layout='none')
        self.assertEqual(warning_log.call_count, 2, 'Only expected warning for overwriting manifest')
        self.assertEqual(download_func.call_count, len(self.manifest) - 1)
        self._assert_all_files_downloaded()
        self._assert_manifest_updated_with_paths('')

    def _test_download_dir(self, download_dir):
        download_func = self._mock_download_manifest(self.manifest_file, 'aws', layout='none', download_dir=download_dir)
        self.assertEqual(download_func.call_count, len(self.manifest) - 1)
        # Since files now exist, running again ensures that we avoid unnecessary downloads
        self._mock_download_manifest(self.manifest_file, 'aws', layout='none', download_dir=download_dir)
        self.assertEqual(download_func.call_count, len(self.manifest) - 1)
        self._assert_all_files_downloaded(prefix=download_dir)
        self._assert_manifest_updated_with_paths(download_dir)

    def test_download_dir_empty(self):
        self._test_download_dir('')

    def test_download_dir_dot(self):
        self._test_download_dir('.')

    def test_download_dir(self):
        self._test_download_dir('a_nested_dir')

    def test_download_dir_dot_dir(self):
        self._test_download_dir(os.path.join('.', 'a_nested_dir'))

    @patch('logging.Logger.warning')
    def test_manifest_download_different_path(self, warning_log):
        # Move manifest file so it is not overwritten on download
        os.mkdir('my_manifest_dir')
        new_manifest_path = os.path.join('my_manifest_dir', self.manifest_file)
        os.rename(self.manifest_file, new_manifest_path)
        self.manifest_file = new_manifest_path
        download_func = self._mock_download_manifest(self.manifest_file, 'aws', layout='none')
        self.assertEqual(download_func.call_count, len(self.manifest) - 1)
        self.assertEqual(warning_log.call_count, 0)
        # Since files now exist, running again ensures that we avoid unnecessary downloads
        self._mock_download_manifest(self.manifest_file, 'aws', layout='none')
        self.assertEqual(warning_log.call_count, 1, 'Only expected warning for overwriting manifest')
        self.assertEqual(download_func.call_count, len(self.manifest) - 1)
        # Remove the original manifest file for accurate count
        os.remove(new_manifest_path)
        self._assert_all_files_downloaded()
        self._assert_manifest_updated_with_paths('')

    @patch('logging.Logger.warning')
    def test_manifest_download_partial(self, warning_log):
        """Test download when some files are already present"""
        _touch_file(ManifestDownloadContext._file_path(self.manifest[1][4], '.'))
        self._mock_download_manifest(self.manifest_file, 'aws', layout='none')
        self.assertEqual(warning_log.call_count, 1, 'Only expected warning for overwriting manifest')
        self._assert_all_files_downloaded()
        self._assert_manifest_updated_with_paths('')

    @patch('logging.Logger.warning')
    @patch('hca.dss.DownloadContext._download_file', side_effect=[None, ValueError(), KeyError()])
    def test_manifest_download_failed(self, _, warning_log):
        self.assertRaises(RuntimeError, self.dss.download_manifest, self.manifest_file, 'aws', layout='none')
        self.assertEqual(warning_log.call_count, 2)
        self._assert_manifest_not_updated()

    @unittest.skipIf(os.name is 'nt', 'Unable to test on Windows')  # TODO windows testing refactor
    def test_manifest_download_parallel(self):
        """
        The goal is to make sure the download of the file happens simultaneously in multiple threads.

        The approach is to mock the old download_file function with a replacement that runs the same code but waits
        for at least two threads to be ready before beginning.
        """
        self.dss.threads = 3  # 3 threads for three files with barrier size 3
        self._write_uniform_manifest()
        self._mock_download_manifest(self.manifest_file, 'aws', layout='none')
        files_expected = {
            os.path.join('.', 'manifest.tsv'),
            os.path.join('.', self.version_dir, 'fa', 'keha', 'fakehash')
        }
        self.assertEqual(self._files_present(), files_expected)


class TestManifestDownloadBundle(DSSClientTestCase):

    def data_files(self, prefix='.'):
        return {
            os.path.join(prefix, 'a_uuid.1_version', 'a_file_name'),
            os.path.join(prefix, 'b_uuid.1_version', 'b_file_name'),
            os.path.join(prefix, 'c_uuid.1_version', 'c_file_name'),
            os.path.join(prefix, 'c_uuid.1_version', 'bundle.json'),
        }

    def metadata_files(self, prefix='.'):
        return {
            os.path.join(prefix, self.version_dir, '8f', 'fe48', '8ffe4838ac08672041f73f82e5f8361860627271ec31aa479fbb65f2ccc46d05'),
            os.path.join(prefix, 'a_uuid.1_version', 'metadata_file.pdf'),
            os.path.join(prefix, 'b_uuid.1_version', 'metadata_file.pdf'),
            os.path.join(prefix, 'c_uuid.1_version', 'metadata_file.pdf'),
        }

    def _assert_links(self, prefix):
        for linked_file in self.data_files(prefix=prefix):
            self.assertEqual(os.stat(linked_file).st_nlink, 2,
                             'Expected one link for the "filestore" entry and link in bundle download')
        for linked_file in self.metadata_files(prefix=prefix):
            self.assertEqual(os.stat(linked_file).st_nlink, 4,
                             'Expected one link for the "filestore" entry and one for each bundle')

    def _assert_all_files_downloaded(self, more_files=None, prefix=''):
        bundle_files = self.data_files(prefix=prefix).union(self.metadata_files(prefix=prefix))
        more_files = bundle_files.union(more_files) if more_files else bundle_files
        super()._assert_all_files_downloaded(more_files=more_files, prefix=prefix)

    def test_manifest_download_bundle(self):
        self._mock_download_manifest(self.manifest_file, 'aws', layout='bundle')
        self._assert_all_files_downloaded()
        self._mock_download_manifest(self.manifest_file, 'aws', layout='bundle')
        self._assert_all_files_downloaded()
        self._assert_manifest_updated_with_paths('')
        self._assert_links('')

    def _test_download_dir(self, download_dir):
        self._mock_download_manifest(self.manifest_file, 'aws', layout='bundle', download_dir=download_dir)
        self._assert_all_files_downloaded(prefix=download_dir)
        self._mock_download_manifest(self.manifest_file, 'aws', layout='bundle', download_dir=download_dir)
        self._assert_all_files_downloaded(prefix=download_dir)
        self._assert_manifest_updated_with_paths(download_dir)
        self._assert_links(download_dir)
        self._assert_bundle_json(prefix=download_dir)

    def _assert_bundle_json(self, prefix=''):
        prefix = os.path.join(prefix, self.version_dir)
        expected_hash = '2b9c91b0c982e46bc8d3b15f4e01763c5b8f3da52ae501ad3796a4c4566d24c5'
        bundle_json_path = os.path.join(prefix, '2b', '9c91', expected_hash)
        with open(bundle_json_path, 'rb') as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(actual_hash, expected_hash)

    def test_download_dir_empty(self):
        self._test_download_dir('')

    def test_download_dir_dot(self):
        self._test_download_dir('.')

    def test_download_dir(self):
        self._test_download_dir('a_nested_dir')

    def test_download_dir_dot_dir(self):
        self._test_download_dir(os.path.join('.', 'a_nested_dir'))

    def test_manifest_download_bad_file(self):
        """
        Ensure error is raised if a user created file has the same name as the one
        we're trying to download.
        """
        manifest_directory = self.manifest[1][0] + '.' + self.manifest[1][1]
        _touch_file(os.path.join(manifest_directory, self.manifest[1][3]))
        self.assertRaises(RuntimeError, self._mock_download_manifest, self.manifest_file, 'aws', layout='bundle')

    @patch('hca.dss.DSSClient.get_bundle')
    def test_manifest_download_bundle_parallel(self, mock_get_bundle):
        """
        Ensure that if the same file is downloaded by multiple threads at the same time, they all link together in
        the filestore in the end.

        To do this, we download three files from three different bundles that are actually all the same file and
        therefore stored in the same place in the filestore. All share the same `fakehash`.
        """
        random.seed('same seed for consistency')
        self._write_uniform_manifest()
        mock_get_bundle.paginate = _make_fake_paginate(fake_hash=True)
        with patch('hca.dss.DownloadContext._do_download_file', side_effect=_fake_do_download_file_with_barrier):
            # 3 threads for three files with barrier size 3
            with patch('hca.dss.TaskRunner', return_value=TaskRunner(threads=3)):
                self.dss.download_manifest(self.manifest_file, 'aws', layout='bundle', no_metadata=True)
        filestore_copy = os.path.join('.', self.version_dir, 'fa', 'keha', 'fakehash')
        filestore_stat = os.stat(filestore_copy)
        self.assertEqual(filestore_stat.st_nlink, 4)
        inode_id = filestore_stat.st_dev, filestore_stat.st_ino
        for linked_file in [os.path.join(name + '_uuid.1_version', name + '_file_name') for name in ('a', 'b', 'c')]:
            linked_stat = os.stat(linked_file)
            self.assertEqual(inode_id, (linked_stat.st_dev, linked_stat.st_ino))

        self.dss.download_manifest(self.manifest_file, 'aws', layout='bundle')


class TestDownload(DSSClientTestCase):

    def test_download(self):
        self._mock_download('any_bundle_uuid', 'aws')
        more_files = {os.path.join('.', 'any_bundle_uuid', file_name)
                      for file_name in ['a_file_name', 'b_file_name', 'c_file_name', 'metadata_file.pdf']}
        more_files.add(os.path.join(self.version_dir, '8f', 'fe48',
                                    '8ffe4838ac08672041f73f82e5f8361860627271ec31aa479fbb65f2ccc46d05'))
        self._assert_all_files_downloaded(more_files=more_files)

    def test_no_data(self):
        self._test_download_filters(no_data=True, no_metadata=False)

    def test_no_metadata(self):
        self._test_download_filters(no_data=False, no_metadata=True)

    def test_neither_data_nor_metadata(self):
        self._test_download_filters(no_data=True, no_metadata=True)

    def test_both_data_and_metadata(self):
        self._test_download_filters(no_data=False, no_metadata=False)

    def _test_download_filters(self, no_metadata, no_data):
        data_files = {
            os.path.join('.', 'any_bundle_uuid.1_version', 'a_file_name'),
            os.path.join('.', 'any_bundle_uuid.1_version', 'b_file_name'),
            os.path.join('.', 'any_bundle_uuid.1_version', 'c_file_name')
        }
        metadata_files = {os.path.join('.', 'any_bundle_uuid.1_version', 'metadata_file.pdf')}
        all_files = metadata_files.union(data_files)
        self._mock_download('any_bundle_uuid', 'aws', no_metadata=no_metadata, no_data=no_data)
        expected_files = all_files
        if no_data:
            expected_files.difference_update(data_files)
        if no_metadata:
            expected_files.difference_update(metadata_files)
        actual_files = self._files_present()
        for f in expected_files:
            self.assertIn(f, actual_files)
        unexpected_files = all_files.difference(expected_files)
        for f in unexpected_files:
            self.assertNotIn(f, actual_files)

    def test_download_filters_conflict(self):
        with self.assertRaises(ValueError):
            self.dss.download('any_bundle_uuid', 'aws', no_data=True, data_filter=('a_file',))
        with self.assertRaises(ValueError):
            self.dss.download('any_bundle_uuid', 'aws', no_metadata=True, metadata_filter=('a_file',))

    @patch('hca.dss.DSSClient.get_bundle')
    @patch('logging.Logger.warning')
    @patch('hca.dss.DownloadContext._download_file', side_effect=[None, ValueError(), KeyError()])
    def test_manifest_download_failed(self, _, warning_log, mock_get_bundle):
        mock_get_bundle.paginate = _make_fake_paginate()
        self.assertRaises(RuntimeError, self.dss.download, 'any_bundle_uuid', 'aws')
        self.assertEqual(warning_log.call_count, 4)
        self._assert_manifest_not_updated()

    def _test_download_dir(self, download_dir):
        self._mock_download('any_bundle_uuid', 'aws')
        more_files = {os.path.join(download_dir, 'any_bundle_uuid', file_name)
                      for file_name in ['a_file_name', 'b_file_name', 'c_file_name', 'metadata_file.pdf']}
        more_files.add(os.path.join(download_dir, self.version_dir, '8f', 'fe48',
                                    '8ffe4838ac08672041f73f82e5f8361860627271ec31aa479fbb65f2ccc46d05'))
        self._assert_all_files_downloaded(more_files=more_files)
        self._assert_bundle_json()

    def _assert_bundle_json(self):
        expected_hash = '2ec1263c1e48086a47184266e079a0a9207800d2bd6bdfa00182aa9b8ac776bb'
        bundle_json_path = os.path.join(self.version_dir, '2e', 'c126', expected_hash)
        with open(bundle_json_path, 'rb') as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(actual_hash, expected_hash)

    def test_download_dir_empty(self):
        self._test_download_dir('')

    def test_download_dir_dot(self):
        self._test_download_dir('.')

    def test_download_dir(self):
        self._test_download_dir('a_nested_dir')

    def test_download_dir_dot_dir(self):
        self._test_download_dir(os.path.join('.', 'a_nested_dir'))

    @staticmethod
    def _fake_get_collection(collections):
        """Used for mocking :meth:`hca.dss.DSSClient.get_collection`"""
        def func(*args, **kwargs):
            for collection in collections:
                if collection['uuid'] == kwargs['uuid']:
                    return collection
        return func

    @staticmethod
    def _generate_col_hierarchy(depth, child_uuid=None):
        """
        Generate a list of psuedo-collections such that each
        collection (except for the first) is a child of its
        predecessor.
        """
        # If 'child_uuid' is not provided, then it's the first call,
        # which means that we generate the parent ID and the child ID
        # If 'child_uuid' is provided, then it's not the first call,
        # which means that parent_uuid = child_uuid, and we provide a
        skel = {'uuid': child_uuid if child_uuid else str(uuid.uuid4()),
                'version': '2018-09-17T161441.564206Z',  # arbitrary
                'description': 'foo',
                'details': {},
                'name': 'bar',
                'contents': [{
                    'type': 'collection',
                    'uuid': str(uuid.uuid4()),  # overwrite if necessary
                    'version': '2018-09-17T161441.564206Z'}]}  # arbitrary
        if depth == 1:
            # Base case: we don't care about the new child uuid, leave
            # generated uuid in place
            return [skel]
        child_uuid = str(uuid.uuid4())
        skel['contents'][0]['uuid'] = child_uuid
        return [skel] + TestDownload._generate_col_hierarchy(depth - 1, child_uuid)

    @unittest.skipIf(os.name is 'nt', 'Unable to test on Windows')  # TODO windows testing refactor
    def test_collection_download_self_nested(self):
        """
        If a collection contains itself, download should ignore
        "extra" requests to download that collection. If this isn't
        working, execution will either (1) never terminate or (2)
        result in a :exc:`RuntimeError` (see
        :meth:`test_collection_download_nested`).
        """
        # For what it's worth, I can't find a way to create this in the
        # DSS, since I can't create a collection that contains another
        # collection that doesn't yet exist. (And there is no way to
        # update collections after creation.) That said, this purely
        # hypothetical case is handled as it is specified in #339.
        test_col = self._generate_col_hierarchy(1)[0]
        test_col['contents'][0]['uuid'] = test_col['uuid']
        test_col['contents'][0]['version'] = test_col['version']
        mock_get_col = self._fake_get_collection([test_col])
        with tempfile.TemporaryDirectory() as t:
            with patch('hca.dss.DSSClient.get_collection', new=mock_get_col):
                self.dss.download_collection(uuid=test_col['uuid'],
                                             replica='aws', download_dir=t)

    def test_collection_download_deep(self):
        """Test that we can download nested collections"""
        test_cols = self._generate_col_hierarchy(4)
        test_cols[-1]['contents'][0] = {
            'type': 'file',
            'uuid': 'foo',
            'version': 'bar'
        }
        mock_get_col = self._fake_get_collection(test_cols)
        with tempfile.TemporaryDirectory() as t:
            # Currently, we can't download files not associated with a bundle.
            # When that functionality is implemented, we don't need to catch
            # this RuntimeError, which is nice. (Implementing this test
            # with a simulated bundle download is too much work, and tests
            # the same thing - that we can parse nested collections from the
            # head and reach the tail.)
            with self.assertRaises(RuntimeError) as e:
                with patch('hca.dss.DSSClient.get_collection', new=mock_get_col):
                    self.dss.download_collection(uuid=test_cols[0]['uuid'],
                                                 replica='aws', download_dir=t)
            self.assertIn("download failure", e.exception.args[0])


if __name__ == "__main__":
    unittest.main()
