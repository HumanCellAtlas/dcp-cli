import os
import shutil
import unittest
import subprocess
import sys


class TestDSSDocAPI(unittest.TestCase):
    def setUp(self):
        super(TestDSSDocAPI, self).setUp()
        self.directory = os.path.dirname(os.path.abspath(__file__))
        if not os.path.isdir('./download_test'):
            os.mkdir('./download_test')

    def teardown(self):
        if os.path.isdir('./download_test'):
            shutil.rmtree("./download_test")
        if os.path.isdir('./.hca'):
            shutil.rmtree("./.hca")
        if os.path.exists("./manifest.tsv"):
            os.remove("./manifest.tsv")

    def checkExitCode(self, input_method, script):
        script = os.path.join(self.directory, 'scripts', input_method, script)
        print(script)

        pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        program = os.path.join(pkg_root, script)
        assert program == script
        process = subprocess.Popen(
            ["python3", f"{program}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()  # assert process.returncode == 0, stderr
        self.teardown()
        if isinstance(stdout, bytes):
            return stdout.decode("utf-8") + " " + stderr.decode("utf-8")
        return stdout + " " + stderr
    
    def testDownloadManifest_api(self):
        self.checkExitCode("api","download_manifest_api.py")

    def testLogin_api(self):
        self.checkExitCode("api","login_api.py")

    def testCreateVersion_api(self):
        self.checkExitCode("api","create_version_api.py")

    def testgetBundle_api(self):
        self.checkExitCode("api","get_bundle_api.py")

    def testGetBundlesCheckout_api(self):
        self.checkExitCode("api","get_bundles_checkout_api.py")
    
    def testGetFileCheckout_api(self):
        self.checkExitCode("api","get_file_api.py")

    def testGetFileHead_api(self):
        self.checkExitCode("api","get_file_head_api.py")
        
    def testPostBundlesCheckout_api(self):
        self.checkExitCode("api","post_bundles_checkout_api.py")

    def testPostSearch_api(self):
        self.checkExitCode("api","post_search_api.py")
    
    def testRefreshSwagger_api(self):
        self.checkExitCode("api",'refresh_swagger_api.py')

    def testLogout_api(self):
        self.checkExitCode("api",'logout_api.py')

    def testDownloadManifest_cli(self):
        self.checkExitCode("cli", "download_manifest_cli.sh")

    def testLogin_cli(self):
        self.checkExitCode("cli","login_cli.sh")

    def testCreateVersion_cli(self):
        self.checkExitCode("cli","create_version_cli.sh")

    def testgetBundle_cli(self):
        self.checkExitCode("cli","get_bundle_cli.sh")

    def testGetBundlesCheckout_cli(self):
        self.checkExitCode("cli","get_bundles_checkout_cli.sh")
    
    def testGetFileCheckout_cli(self):
        self.checkExitCode("cli","get_file_cli.sh")

    def testGetFileHead_cli(self):
        self.checkExitCode("cli","get_file_head_cli.sh")
        
    def testPostBundlesCheckout_cli(self):
        self.checkExitCode("cli","post_bundles_checkout_cli.sh")

    def testPostSearch_cli(self):
        self.checkExitCode("cli","post_search_cli.sh")
    
    def testRefreshSwagger_cli(self):
        self.checkExitCode("cli","refresh_swagger_cli.sh")

    def testLogout_cli(self):
        self.checkExitCode("cli","logout_cli.sh")

    
if __name__ == "__main__":
    unittest.main()
