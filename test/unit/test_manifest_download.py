import errno
import os
import shutil
import tempfile
import unittest

import scandir
from mock import patch

from hca.dss import DSSClient


def _touch_file(path):
    try:
        os.makedirs(os.path.split(path)[0])
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    with open(path, 'w'):
        pass


def _fake_download(*args, **kwargs):
    _touch_file(args[2])


class TestManifestDownload(unittest.TestCase):
    manifest = list(zip(
        ('bundle_uuid', 'a_uuid', 'b_uuid', 'c_uuid'),
        ('bundle_version', '1_version', '1_version', '1_version'),
        ('file_content_type', 'somestuff', 'somestuff', 'somestuff'),
        ('file_name', 'a_file_name', 'b_file_name', 'c_file_name'),
        ('file_sha256',
         'ad3fc1e4898e0bce096be5151964a81929dbd2a92bd5ed56a39a8e133053831d',
         '8f35071eaeedd9d6f575a8b0f291daeac4c1dfdfa133b5c561232a00bf18c4b4',
         '8f3404db04bdede03e9128a4b48599d0ecde5b2e58ed9ce52ce84c3d54a3429c'),
        ('file_size', '12', '2', '41'),
        ('file_uuid', 'af_uuid', 'bf_uuid', 'cf_uuid'),
        ('file_version', 'af_version', 'af_version', 'af_version'),
        ('file_indexed', 'False', 'False', 'False'),
    ))

    def setUp(self):
        self.prev_wd = os.getcwd()
        self.tmp_dir = tempfile.mkdtemp()
        os.chdir(self.tmp_dir)
        self.dss = DSSClient()
        with open('manifest.tsv', 'w') as f:
            f.write('\n'.join(['\t'.join(row) for row in self.manifest]))

    def tearDown(self):
        os.chdir(self.prev_wd)
        shutil.rmtree(self.tmp_dir)

    def _assert_all_files_downloaded(self):
        files_present = {os.path.join(dir_path, f)
                         for dir_path, _, files in scandir.walk('.')
                         for f in files}
        files_expected = {
            os.path.join('.', 'manifest.tsv'),
            os.path.join('.', 'ad', '3fc1', 'ad3fc1e4898e0bce096be5151964a81929dbd2a92bd5ed56a39a8e133053831d'),
            os.path.join('.', '8f', '3507', '8f35071eaeedd9d6f575a8b0f291daeac4c1dfdfa133b5c561232a00bf18c4b4'),
            os.path.join('.', '8f', '3404', '8f3404db04bdede03e9128a4b48599d0ecde5b2e58ed9ce52ce84c3d54a3429c'),
        }
        self.assertEqual(files_present, files_expected)

    @patch('hca.dss.DSSClient.DIRECTORY_NAME_LENGTHS', [1, 2, 3])
    def test_file_path(self):
        self.assertRaises(AssertionError, self.dss._file_path, 'a')
        parts = self.dss._file_path('abcdefghij').split(os.sep)
        self.assertEqual(parts, ['a', 'bc', 'def', 'abcdefghij'])

    @patch('hca.dss.DSSClient._download_file', side_effect=_fake_download)
    def test_manifest_download(self, download_func):
        self.dss.download_manifest_v2('manifest.tsv', 'aws')
        self.assertEqual(download_func.call_count, len(self.manifest) - 1)
        # Since files now exist, running again ensures that we avoid unnecessary downloads
        self.dss.download_manifest_v2('manifest.tsv', 'aws')
        self.assertEqual(download_func.call_count, len(self.manifest) - 1)
        self._assert_all_files_downloaded()

    @patch('hca.dss.DSSClient._download_file', side_effect=_fake_download)
    def test_manifest_download_partial(self, _):
        _touch_file(self.dss._file_path(self.manifest[1][4]))
        self.dss.download_manifest_v2('manifest.tsv', 'aws')
        self._assert_all_files_downloaded()

    @patch('logging.Logger.warning')
    @patch('hca.dss.DSSClient._download_file', side_effect=[None, ValueError(), KeyError()])
    def test_manifest_download_failed(self, download_func, warning_log):
        self.assertRaises(RuntimeError, self.dss.download_manifest_v2, 'manifest.tsv', 'aws')
        self.assertEqual(warning_log.call_count, 2)


if __name__ == "__main__":
    unittest.main()
