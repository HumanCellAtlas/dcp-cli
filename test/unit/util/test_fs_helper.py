#!/usr/bin/env python
# coding: utf-8

import os
import sys
import errno
import warnings
import unittest

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from hca.util.fs_helper import FSHelper
from hca.util.compat import USING_PYTHON2

if USING_PYTHON2:
    import mock
else:
    from unittest import mock


class TestFSHelper(unittest.TestCase):

    def test_atomic_write(self):
        filename = "some_file"
        dir = "/some/dir"
        content = "some content"
        err = EnvironmentError()
        with mock.patch('tempfile.NamedTemporaryFile') as mock_named_temporary_file, \
                mock.patch('hca.util.fs._atomic_rename') as mock_atomic_rename, \
                mock.patch('os.path.isfile') as mock_isfile, \
                mock.patch('os.remove') as mock_remove, \
                warnings.catch_warnings(record=True) as warn:
            mock_temp_file = mock_named_temporary_file().__enter__()
            mock_temp_file.name = "temp_name"
            mock_isfile.return_value = True

            FSHelper.atomic_write(filename, dir, content)
            self.assertTrue(mock_temp_file.write.calledWith(content))
            self.assertTrue(mock_atomic_rename.calledWith(mock_temp_file.name, filename))
            self.assertTrue(mock_remove.calledWith(mock_temp_file.name))
            self.assertTrue(len(warn) == 0)

            mock_remove.side_effect = err
            FSHelper.atomic_write(filename, dir, content)
            self.assertTrue(len(warn) == 1)

    def test_atomic_rename_ok(self):
        src = "src"
        dest = "dest"
        with mock.patch('os.rename') as mock_rename, \
                mock.patch('os.remove') as mock_remove:
            FSHelper._atomic_rename(src, dest)
            self.assertTrue(mock_rename.calledWith(src, dest))
            self.assertFalse(mock_remove.called)

    def test_atomic_rename_file_exists_error(self):
        src = "src"
        dest = "dest"
        max_retries = 5
        with mock.patch('os.rename') as mock_rename, \
                mock.patch('hca.util.fs._handle_rename_error') as mock_handle_rename_error, \
                warnings.catch_warnings(record=True) as warn:
            err = OSError()
            mock_rename.side_effect = err
            FSHelper._atomic_rename(src, dest)
            self.assertTrue(mock_rename.calledWith(src, dest))
            self.assertEqual(mock_handle_rename_error.call_count, max_retries)
            self.assertTrue(len(warn) == 1)

    def test_handle_rename_windows_error(self):
        src = "src"
        dest = "dest"
        err = OSError()
        err.errno = errno.EEXIST
        with mock.patch('os.remove') as mock_remove:
            FSHelper._handle_rename_error(err, src, dest)
            self.assertTrue(mock_remove.calledWith(dest))

    def test_handle_rename_unknown_error(self):
        src = "src"
        dest = "dest"
        err = OSError()
        with mock.patch('os.remove') as mock_remove:
            self.assertRaises(Exception, FSHelper._handle_rename_error, err, src, dest)
            self.assertFalse(mock_remove.called)

    def test_get_days_since_last_modified(self):
        file = "file"
        with mock.patch('os.path.getmtime') as mock_getmtime:
            FSHelper.get_days_since_last_modified(file)
            self.assertTrue(mock_getmtime.calledWith(file))


if __name__ == "__main__":
    unittest.main()
