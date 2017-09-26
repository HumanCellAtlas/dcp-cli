from __future__ import absolute_import, division, print_function, unicode_literals

import os
import time
import uuid
from io import open

import requests

import hca.dss
from ... import infra
from ...upload_to_cloud import upload_to_cloud
from ...added_command import AddedCommand


class Upload(AddedCommand):
    """
    Functions needed to fully add this functionality to the command line parser.

    This is functional at the moment but not the best ux. Will refactor that in a later diff.
    """

    FILE_OR_DIR_ARGNAME = "file_or_dir"
    CREATOR_ID_ENVIRONMENT_VARIABLE = "creator_uid"
    BACKOFF_FACTOR = 1.618
    """The time we wait while we poll during an async upload increases by this factor each iteration."""

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
        logger = infra.get_logger(Upload)
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
        # Close file handles in files_to_upload. s3 paths are strings, so don't count those.
        for file_handle in filter(lambda x: not isinstance(x, str), files_to_upload):
            file_handle.close()
        filenames = list(map(os.path.basename, uploaded_keys))

        # Print to stderr, upload the files to s3 and return a list of tuples: (filename, filekey)
        logger.info("%s", "Uploading the following keys to aws:")
        logger.info("%s", " " + " ".join(filenames))

        filename_key_list = list(zip(filenames, file_uuids, uploaded_keys))
        logger.info("%s", "The following keys were uploaded successfully:")
        logger.info("%s", " " + " ".join(["\n{:<12}  {:<12}".format(filename, key)
                                          for filename, file_uuid, key in filename_key_list]))
        return filename_key_list

    @classmethod
    def _put_files(cls, filename_key_list, staging_bucket, timeout_seconds=1200):
        """Make a put-files request on each of these files using the python bindings."""
        logger = infra.get_logger(Upload)

        bundle_uuid = str(uuid.uuid4())
        files = []
        for filename, file_uuid, key in filename_key_list:
            logger.info("%s", "File {}: registering...".format(filename))

            # Generating file data
            creator_uid = os.environ.get(cls.CREATOR_ID_ENVIRONMENT_VARIABLE, 1)
            source_url = "s3://{}/{}".format(staging_bucket, key)
            logger.info("%s", "File {}: registering from {} -> uuid {}".format(
                filename, source_url, file_uuid))

            response = hca.dss.put_files(
                file_uuid,
                bundle_uuid=bundle_uuid,
                creator_uid=creator_uid,
                source_url=source_url,
                stream=True,
            )

            try:
                logger.debug("%s", "File {}: Response: {}".format(filename, response.content.decode()))

                if response.status_code in (requests.codes.ok, requests.codes.created, requests.codes.accepted):
                    version = response.json().get('version', "blank")
                    files.append({
                        'name': filename,
                        'version': version,
                        'uuid': file_uuid,
                        'creator_uid': creator_uid
                    })

                if response.status_code in (requests.codes.ok, requests.codes.created):
                    logger.info("%s", "File {}: Sync copy -> {}".format(filename, version))
                elif response.status_code == requests.codes.accepted:
                    logger.info("%s", "File {}: Async copy -> {}".format(filename, version))

                    timeout = time.time() + timeout_seconds
                    wait = 1.0
                    while time.time() < timeout:
                        get_resp = hca.dss.head_files(file_uuid, version)
                        if get_resp.ok:
                            break
                        time.sleep(wait)
                        wait = min(60.0, wait * Upload.BACKOFF_FACTOR)
                    else:
                        # timed out. :(
                        raise RuntimeError("File {}: registration FAILED".format(filename))
                    logger.debug("%s", "Successfully fetched file")
                else:
                    logger.error("%s", "File {}: Registration FAILED".format(filename))
                    logger.error("%s", "Response: {}".format(response.text))
                    response.raise_for_status()
            finally:
                response.close()

        return bundle_uuid, files

    @classmethod
    def _put_bundle(cls, bundle_uuid, files, replica):
        """Make a put-bundles request using the python bindings."""
        logger = infra.get_logger(Upload)

        creator_uid = os.environ.get(cls.CREATOR_ID_ENVIRONMENT_VARIABLE, 1)
        file_args = [{'indexed': True,
                      'name': file_['name'],
                      'version': file_['version'],
                      'uuid': file_['uuid']} for file_ in files]

        logger.info("%s", "Bundle {}: Registering...".format(bundle_uuid))

        response = hca.dss.put_bundles(bundle_uuid, replica=replica, creator_uid=creator_uid, files=file_args)
        try:
            logger.debug("%s", "Bundle {}: Response: {}".format(bundle_uuid, response.content.decode()))

            if response.ok:
                version = response.json().get('version')
                logger.info("%s", "Bundle {}: Registered successfully".format(bundle_uuid))
            else:
                logger.info("%s", "Bundle {}: Registration failed".format(bundle_uuid))
                logger.info("%s", "Response: {}".format(response.text))
                response.raise_for_status()
        finally:
            response.close()

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
    def run_from_cli(cls, args):
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
