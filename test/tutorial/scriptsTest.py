import os
import shutil
import unittest
import subprocess
import re


class TestDSSDocAPI(unittest.TestCase):
    def setUp(self):
        super(TestDSSDocAPI, self).setUp()
        self.directory = os.path.dirname(os.path.abspath(__file__))
        if not os.path.isdir("./download_test"):
            os.mkdir("./download_test")

    def teardown(self):
        if os.path.isdir("./download_test"):
            shutil.rmtree("./download_test")
        if os.path.isdir("./.hca"):
            shutil.rmtree("./.hca")
        if os.path.exists("./manifest.tsv"):
            os.remove("./manifest.tsv")

    def checkExitCode(self, input_method, script):
        script = os.path.join('/', self.directory, "scripts", input_method, script)
        print("\n"+script)

        pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        program = os.path.join(pkg_root, script)
        assert program == script
        if input_method == "api":
            process = subprocess.Popen(
                ["python3", f"{program}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        else:
            process = subprocess.Popen(
                ["bash", f"{program}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        stdout, stderr = process.communicate()
        self.teardown()
        if len(stderr) > 0:
            print(stderr.decode("utf-8"))
        if isinstance(stdout, bytes):
            return stdout.decode("utf-8") + " " + stderr.decode("utf-8")
        return stdout + " " + stderr

    def checkExpectedOut(self, input_method, script, expectedOutput):
        outerr = self.checkExitCode(input_method, script)
        index = outerr.replace('"', "").find(expectedOutput)
        self.assertGreater(index, -1, index)

    def checkExpectedPattern(self, input_method, script, pattern):
        outerr = self.checkExitCode(input_method, script)
        pattern = re.compile(pattern, re.DOTALL)
        n = re.search(pattern, outerr)
        self.assertNotEqual(n, None, n)

    def testDownloadManifest_api(self):
        self.checkExpectedOut(
            "api", "download_manifest_api.py", "Overwriting manifest manifest.tsv"
        )

    def testLogin_api(self):
        self.checkExpectedOut("api", "login_api.py", "Storing access credentials")

    def testCreateVersion_api(self):
        self.checkExpectedPattern(
            "api",
            "create_version_api.py",
            "[0-9]{4}-[0-9]{2}-[A-Za-z0-9]{9}.[A-Za-z0-9]{7}",
        )

    def testgetBundle_api(self):
        self.checkExpectedOut("api", "get_bundle_api.py", "content-type")

    def testGetBundlesCheckout_api(self):
        self.checkExpectedOut("api", "get_bundles_checkout_api.py", "status")

    def testGetFile_api(self):
        self.checkExpectedOut("api", "get_file_api.py", "type")

    def testGetFileHead_api(self):
        self.checkExpectedOut(
            "api", "get_file_head_api.py", "<Response [200]>\n<Response [200]>"
        )

    def testPostBundlesCheckout_api(self):
        self.checkExpectedOut("api", "post_bundles_checkout_api.py", "checkout_job_id")

    def testPostSearch_api(self):
        self.checkExpectedOut("api", "post_search_api.py", "bundle_fqid")

    def testRefreshSwagger_api(self):
        self.checkExitCode("api", "refresh_swagger_api.py")

    def testDownload_api(self):
        self.checkExitCode("api", "download_api.py")

    def testLogout_api(self):
        self.checkExitCode("api", "logout_api.py")

    def testDownloadManifest_cli(self):
        self.checkExpectedOut(
            "cli", "download_manifest_cli.sh", "Overwriting manifest manifest.tsv"
        )

    def testLogin_cli(self):
        self.checkExpectedOut("cli", "login_cli.sh", "Storing access credentials")

    def testCreateVersion_cli(self):
        self.checkExpectedPattern(
            "cli",
            "create_version_cli.sh",
            "[0-9]{4}-[0-9]{2}-[A-Za-z0-9]{9}.[A-Za-z0-9]{7}",
        )

    def testgetBundle_cli(self):
        self.checkExpectedOut("cli", "get_bundle_cli.sh", "content-type")

    def testGetBundlesCheckout_cli(self):
        self.checkExpectedOut("cli", "get_bundles_checkout_cli.sh", "status")

    def testGetFile_cli(self):
        self.checkExpectedOut("cli", "get_file_cli.sh", "describedBy")

    def testGetFileHead_cli(self):
        self.checkExpectedOut(
            "cli", "get_file_head_cli.sh", "<Response [200]>\n<Response [200]>"
        )

    def testPostBundlesCheckout_cli(self):
        self.checkExpectedOut("cli", "post_bundles_checkout_cli.sh", "checkout_job_id")

    def testPostSearch_cli(self):
        self.checkExpectedOut("cli", "post_search_cli.sh", "bundle_fqid")

    def testRefreshSwagger_cli(self):
        self.checkExitCode("cli", "refresh_swagger_cli.sh")

    def testDownload_cli(self):
        self.checkExitCode("cli", "download_cli.sh")

    def testLogout_cli(self):
        self.checkExitCode("cli", "logout_cli.sh")

   
# ---------------------------------------
# NEEDS .DEV/ PROPER CREDENTIALS TO TEST
# ---------------------------------------

    # def testPutBundle_api(self):
    #     self.checkExitCode("api", "put_bundle_api.py")

    # def testUpload_api(self):
    #    self.checkExpectedOut("api", "upload_api.py", "Upload successful")

    # def testCollections_api(self):
    #     self.checkExpectedOut("api", "put_delete_get_patch_collection_api.py", "collections")

    # def testDelteBundle_api(self):
    #     self.checkExpectedOut("api", "delete_bundle_api.py", "{}")

    # def testPatchBundle_api(self):
    #     self.checkExitCode("api", "patch_bundle_api.py")

    # def testSubscriptions_api(self):
    #     self.checkExpectedOut("api", "put_delete_get_sub_api.py", "subscriptions")
    
    # def testPutFile_api(self):
    #     self.checkExitCode("api", "put_file_api.py")

    # def testPutBundle_cli(self):
    #     self.checkExitCode("cli", "put_bundle_cli.sh")

    # def testUpload_cli(self):
    #    self.checkExpectedOut("cli", "upload_cli.sh", "bundle_uuid")

    # def testCollections_cli(self):
    #     self.checkExpectedOut("cli", "put_delete_get_patch_collection_cli.sh", "collections")

    # def testPatchBundle_cli(self):
    #     self.checkExitCode("cli", "patch_bundle_cli.sh")

    # def testDeleteBundle_cli(self):
    #     self.checkExpectedOut("cli", "delete_bundle_cli.sh", "{}")

    # def testSubscriptions_cli(self):
    #     self.checkExpectedOut("cli","put_delete_get_sub_cli.sh","subscriptions")

    # def testPutFile_cli(self):
    #     self.checkExitCode("cli", "put_file_cli.sh")
    
if __name__ == "__main__":
    unittest.main()

