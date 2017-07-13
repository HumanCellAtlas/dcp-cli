from __future__ import absolute_import, division, print_function, unicode_literals

import os
import pprint
import sys
import uuid
import logging
from io import open

import boto3

from .constants import Constants
from .upload_to_cloud import upload_to_cloud


class FullUpload:
    """Functions needed to fully add this functionality to the command line parser."""

    CONSOLE_ARGUMENT = "upload"
    FILE_OR_DIR_ARGNAME = "file_or_dir"
    CREATOR_ID_ENVIRONMENT_VARIABLE = "creator_uid"
    REPLICA_ARGNAME = "--replica"

    @classmethod
    def add_parser(cls, subparsers):
        """Call from parser.py to create the parser."""
        subparser = subparsers.add_parser(
            cls.CONSOLE_ARGUMENT,
            help="Upload a file or directory to the cloud, register each of the files, and bundle them together."
        )

        subparser.add_argument(
            cls.FILE_OR_DIR_ARGNAME,
            nargs="+",
            help="Relative or direct path to folder with all bundle files. Alternatively, user can provide a url \
            to an s3 bucket containing a bundle. S3 files must have checksum tags already calculated and assigned."
        )

        subparser.add_argument(
            "--staging-bucket",
            help="Bucket within replica to upload to."
        )

        subparser.add_argument(
            "--replica",
            help="Which cloud to upload to first. One of 'aws', 'gcp', or 'azure'.",
            choices=['aws', 'gcp', 'azure'],
            default="aws"
        )
        return True

    @classmethod
    def _upload_files(cls, args, staging_bucket):
        files_to_upload = []
        from_cloud = False
        for path in args[cls.FILE_OR_DIR_ARGNAME]:
            # Path is s3 url
            if path[:5] == "s3://":
                from_cloud = True
                files_to_upload.append(path)

            # If the path is a directory, add all files in the directory to the bundle
            elif os.path.isdir(path):
                for filename in os.listdir(path):
                    full_file_name = os.path.join(path, filename)
                    files_to_upload.append(open(full_file_name, "rb"))
            else:  # It's a file
                files_to_upload.append(open(path, "rb"))

        file_uuids, uploaded_keys = upload_to_cloud(files_to_upload, staging_bucket, args['replica'], from_cloud)
        filenames = list(map(os.path.basename, uploaded_keys))

        # Print to stderr, upload the files to s3 and return a list of tuples: (filename, filekey)
        logging.info("Uploading the following keys to aws:")
        for file_ in filenames:
            logging.info(file_)

        filename_key_list = list(zip(filenames, file_uuids, uploaded_keys))
        logging.info("\nThe following keys were uploaded successfully:")
        for filename, file_uuid, key in filename_key_list:
            logging.info('{:<12}  {:<12}'.format(filename, key))
        return filename_key_list

    @classmethod
    def _put_files(cls, filename_key_list, staging_bucket, api):
        """Use the API class to make a put-files request on each of these files."""
        bundle_uuid = str(uuid.uuid4())
        files = []
        for filename, file_uuid, key in filename_key_list:
            logging.info("File {}: registering...".format(filename))

            # Generating file data
            creator_uid = os.environ.get(cls.CREATOR_ID_ENVIRONMENT_VARIABLE, "1")
            source_url = "s3://{}/{}".format(staging_bucket, key)
            logging.info(source_url)
            # file_uuid = key[:key.find("/")]
            logging.info("File {}: assigned uuid {}".format(filename, file_uuid))

            response = api.make_request([
                "put-files",
                file_uuid,
                "--bundle-uuid", bundle_uuid,
                "--creator-uid", creator_uid,
                "--source-url", source_url
            ], stream=True)

            if response.ok:
                version = response.json().get('version', "blank")
                logging.info("File {}: registered with uuid {}".format(filename, file_uuid))
                files.append({
                    'name': filename,
                    'version': version,
                    'uuid': file_uuid,
                    'creator_uid': creator_uid
                })
                response.close()

            else:
                logging.info("File {}: registration FAILED".format(filename))
                logging.info(response.text)
                response.close()
                response.raise_for_status()

            logging.info("Request response")
            logging.info("{}".format(response.content.decode()))
        return bundle_uuid, files

    @classmethod
    def _put_bundle(cls, bundle_uuid, files, api, replica):
        """Use the API class to make a put-bundles request."""
        file_args = [Constants.OBJECT_SPLITTER.join([
            "True",
            file['name'],
            file['uuid'],
            file['version']]) for file in files]
        creator_uid = os.environ.get(cls.CREATOR_ID_ENVIRONMENT_VARIABLE, "1")

        logging.info("Bundle {}: registering...".format(bundle_uuid))
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
            version = response.json().get('version', None)
            logging.info("Bundle {}: registered successfully".format(bundle_uuid))

        else:
            logging.info("Bundle {}: registration FAILED".format(bundle_uuid))
            logging.info(response.text)
            response.raise_for_status()

        logging.info("Request response:")
        logging.info("{}\n".format(response.content.decode()))
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
        Bring a bundle from local to the blue box.

        Step 1: Upload the files to s3.
        Step 2: Put the files in the blue box with a shared bundle_uuid.
        Step 3: Put all uploaded files into a bundle together.
        """
        first_url = args['file_or_dir'][0]
        # If there's a staging bucket input, set staging bucket to that.
        # Otherwise grab it from the s3 url.
        staging_bucket = args.get('staging_bucket', first_url[5: first_url.find("/", 5)])

        filename_key_list = cls._upload_files(args, staging_bucket)
        bundle_uuid, files = cls._put_files(filename_key_list, staging_bucket, api)
        final_return = cls._put_bundle(bundle_uuid, files, api, args["replica"])
        return final_return
