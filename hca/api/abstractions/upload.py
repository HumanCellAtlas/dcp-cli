from __future__ import absolute_import, division, print_function, unicode_literals

import os
import pprint
import sys
import uuid
import logging
from io import open

import boto3

from ...upload_to_cloud import upload_to_cloud
from . import put_bundles, put_files
from ...added_command import AddedCommand


class Upload(AddedCommand):
    """Functions needed to fully add this functionality to the command line parser."""

    FILE_OR_DIR_ARGNAME = "file_or_dir"
    CREATOR_ID_ENVIRONMENT_VARIABLE = "creator_uid"

    @classmethod
    def _get_endpoint_info(cls):
        return {
            'body_params': {},
            'description': "Upload a file or directory to the cloud, register each file, and bundle them together.",
            'options': {
                cls.FILE_OR_DIR_ARGNAME: {
                    'description': "List of paths to local/cloud files or a local directory to upload.",
                    'type': "string",
                    'metavar': None,
                    'required': True,
                    'array': True
                    # 'files': {
                    #     'description': "List of paths to files to upload.",
                    #     'type': "string",
                    #     'metavar': None,
                    #     'required': False,
                    #     'array': True
                    # },
                    # 'directory': {
                    #     'description': "Path to directory to upload.",
                    #     'type': "string",
                    #     'metavar': None,
                    #     'required': False,
                    #     'array': False
                    # },
                    # 'cloud_urls': {
                    #     'description': ("List of cloud-hosted files to upload. Currently only supports s3 files. "
                    #                     "Files must have checksum tags already calculated and assigned."),
                    #     'type': "string",
                    #     'metavar': None,
                    #     'required': False,
                    #     'array': True
                },
                'staging_bucket': {  # TODO Mackey22: Check that option names are saved with snake case.
                    'description': "Bucket within replica to upload to.",
                    'type': "string",
                    'metavar': None,
                    'required': False,
                    'array': False
                },
                'replica': {
                    'description': "Which cloud to upload to first. One of 'aws', 'gcp', or 'azure'.",
                    'type': "string",
                    'metavar': None,
                    'required': False,
                    'array': False,
                    'default': "aws",
                }
            }
        }

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
    def _put_files(cls, filename_key_list, staging_bucket):
        """Make a put-files request on each of these files using the python bindings."""
        bundle_uuid = str(uuid.uuid4())
        files = []
        for filename, file_uuid, key in filename_key_list:
            logging.info("File {}: registering...".format(filename))

            # Generating file data
            creator_uid = os.environ.get(cls.CREATOR_ID_ENVIRONMENT_VARIABLE, 1)
            source_url = "s3://{}/{}".format(staging_bucket, key)
            logging.info(source_url)
            # file_uuid = key[:key.find("/")]
            logging.info("File {}: assigned uuid {}".format(filename, file_uuid))

            response = put_files(file_uuid,
                                 bundle_uuid=bundle_uuid,
                                 creator_uid=creator_uid,
                                 source_url=source_url,
                                 stream=True)

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
    def _put_bundle(cls, bundle_uuid, files, replica):
        """Make a put-bundles request using the python bindings."""
        creator_uid = os.environ.get(cls.CREATOR_ID_ENVIRONMENT_VARIABLE, 1)
        file_args = [{'indexed': True,
                      'name': file_['name'],
                      'version': file_['version'],
                      'uuid': file_['uuid']} for file_ in files]

        logging.info("Bundle {}: registering...".format(bundle_uuid))

        response = put_bundles(bundle_uuid, replica=replica, creator_uid=creator_uid, files=file_args)

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
    def run_cli(cls, args):
        """Deposit a bundle from local or remote bucket to blue box with arguments given from cli."""
        return cls.run(args)

    @classmethod
    def run(cls, args):
        """
        Bring a bundle from local to the blue box.

        Step 1: Upload the files to s3.
        Step 2: Put the files in the blue box with a shared bundle_uuid.
        Step 3: Put all uploaded files into a bundle together.
        """
        first_url = args[cls.FILE_OR_DIR_ARGNAME][0]
        # If there's a staging bucket input, set staging bucket to that.
        # Otherwise grab it from the s3 url.
        staging_bucket = args.get('staging_bucket', first_url[5: first_url.find("/", 5)])

        filename_key_list = cls._upload_files(args, staging_bucket)
        bundle_uuid, files = cls._put_files(filename_key_list, staging_bucket)
        final_return = cls._put_bundle(bundle_uuid, files, args["replica"])
        return final_return
