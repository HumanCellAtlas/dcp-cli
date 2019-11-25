import os
import shutil
import tempfile
import unittest


class TmpDirTestCase(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.prev_wd = os.getcwd()
        self.tmp_dir = tempfile.mkdtemp()
        os.chdir(self.tmp_dir)

    def tearDown(self):
        os.chdir(self.prev_wd)
        shutil.rmtree(self.tmp_dir)
        super().tearDown()
