from __future__ import absolute_import, division, print_function, unicode_literals

import os
import pprint
import sys
import uuid

from io import open

from .constants import Constants
from .upload_to_cloud import upload_to_cloud


def eprint(*args, **kwargs):
    """Print to stderr."""
    print(*args, file=sys.stderr, **kwargs)


class FullUpload:
    """Functions needed to create the end-to-end parser and actually run the demo."""

    CONSOLE_ARGUMENT = "upload"
    FILE_OR_DIR_ARGNAME = "file_or_dir"
    CREATOR_ID_ENVIRONMENT_VARIABLE = "creator_uid"
    DEMO_REPLICA_ARGNAME = "--replica"

    @classmethod
    def add_parser(cls, subparsers):
        """Call from parser.py to create the parser to run the demo."""
        subparser = subparsers.add_parser(
            cls.CONSOLE_ARGUMENT,
            help="Upload a file or directory to the cloud, register each of the files, and bundle them together."
        )

        subparser.add_argument(
            cls.FILE_OR_DIR_ARGNAME,
            nargs="+",
            help="Relative or direct path to folder with all bundle files."
        )

        subparser.add_argument(
            cls.DEMO_REPLICA_ARGNAME,
            help="Which cloud to upload to first. One of 'aws', 'gc', or 'azure'.",
            default="aws"
        )
        subparser.add_argument(
            "--staging-bucket",
            help="Bucket within replica to upload to.",
            default="hca-dcp-staging-test")
        return True

    @classmethod
    def _upload_files(cls, args):
        filenames = []
        files_to_upload = []
        for path in args[cls.FILE_OR_DIR_ARGNAME]:

            # If the path is a directory, add all files in the directory to the bundle
            if os.path.isdir(path):
                for filename in os.listdir(path):
                    full_file_name = os.path.join(path, filename)
                    filenames.append(filename)
                    files_to_upload.append(open(full_file_name, "rb"))
            else:  # It's a file
                filenames.append(os.path.basename(path))
                files_to_upload.append(open(path, "rb"))

        # Print to stderr, upload the files to s3 and return a list of tuples: (filename, filekey)
        eprint("Uploading the following keys to aws:")
        for file in filenames:
            eprint("\t", file)

        uploaded_keys = upload_to_cloud(files_to_upload, args["staging_bucket"], args["replica"])

        filename_key_list = list(zip(filenames, uploaded_keys))
        eprint("\nThe following keys were uploaded successfuly:")
        for filename, key in filename_key_list:
            eprint('\t{:<12}  {:<12}'.format(filename, key))
        return filename_key_list

    @classmethod
    def _put_files(cls, filename_key_list, staging_bucket, api):
        """Use the API class to make a put-files request on each of these files."""
        bundle_uuid = str(uuid.uuid4())
        files = []
        for (filename, key) in filename_key_list:
            eprint("File {}: registering...".format(filename))

            # Generating file data
            creator_uid = os.environ.get(cls.CREATOR_ID_ENVIRONMENT_VARIABLE, "1")
            source_url = "s3://{}/{}".format(staging_bucket, key)
            file_uuid = key[:key.find("/")]
            eprint("File {}: assigned uuid {}".format(filename, file_uuid))

            response = api.make_request([
                "put-files",
                file_uuid,
                "--bundle-uuid", bundle_uuid,
                "--creator-uid", creator_uid,
                "--source-url", source_url
            ], stream=True)

            if response.ok:
                version = response.json().get("version", "blank")
                eprint("File {}: registered with uuid {}".format(filename, file_uuid))
                files.append({
                    "name": filename,
                    "version": version,
                    "uuid": file_uuid,
                    "creator_uid": creator_uid
                })
                response.close()

            else:
                eprint("File {}: registration FAILED".format(filename))
                eprint(response.text)
                response.close()
                response.raise_for_status()

            eprint("Request response")
            eprint("{}".format(response.content.decode()))
        return bundle_uuid, files

    @classmethod
    def _put_bundle(cls, bundle_uuid, files, api):
        """Use the API class to make a put-bundles request."""
        file_args = [Constants.OBJECT_SPLITTER.join(["True", file["name"], file["uuid"], file["version"]]) for file in files]
        creator_uid = os.environ.get(cls.CREATOR_ID_ENVIRONMENT_VARIABLE, "1")
        replica = "aws"

        eprint("Bundle {}: registering...".format(bundle_uuid))
        request = [
            "put-bundles",
            bundle_uuid,
            "--replica", replica,
            "--creator-uid", creator_uid,
            "--files"
        ]
        request.extend(file_args)  # file_args is already a list.
        response = api.make_request(request)

        version = None

        if response.ok:
            version = response.json().get("version", "blank")
            eprint("Bundle {}: registered successfully".format(bundle_uuid))

        else:
            eprint("Bundle {}: registration FAILED".format(bundle_uuid))
            eprint(response.text)
            response.raise_for_status()

        eprint("Request response:")
        eprint("{}\n".format(response.content.decode()))
        final_return = {
            "bundle_uuid": bundle_uuid,
            "creator_uid": creator_uid,
            "replica": replica,
            "version": version,
            "files": files,
            "success": response.ok
        }
        return final_return

    @classmethod
    def run(cls, args, api):
        """
        Run through full demo functionality.

        Step 1: Upload the files to s3.
        Step 2: Put the files in the blue box with a shared bundle_uuid.
        Step 3: Put all uploaded files into a bundle together.
        """
        filename_key_list = cls._upload_files(args)
        bundle_uuid, files = cls._put_files(filename_key_list, args["staging_bucket"], api)
        final_return = cls._put_bundle(bundle_uuid, files, api)
        return final_return
