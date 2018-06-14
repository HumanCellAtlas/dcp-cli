from __future__ import absolute_import, division, print_function, unicode_literals

import hashlib
import os
import re
import time
import uuid
from io import open

import requests
from requests.exceptions import ChunkedEncodingError, ConnectionError, ReadTimeout

from ..util import SwaggerClient
from ..util.exceptions import SwaggerAPIException
from .. import logger
from .upload_to_cloud import upload_to_cloud


class DSSClient(SwaggerClient):
    """
    Client for the Data Storage Service API.
    """
    UPLOAD_BACKOFF_FACTOR = 1.618
    def __init__(self, *args, **kwargs):
        super(DSSClient, self).__init__(*args, **kwargs)
        self.commands += [self.download, self.upload]

    def download(self, bundle_uuid, replica, version="", dest_name="", initial_retries_left=10, min_delay_seconds=0.25):
        """
        Download a bundle and save it to the local filesystem as a directory.
        """
        if not dest_name:
            dest_name = bundle_uuid

        bundle = self.get_bundle(uuid=bundle_uuid, replica=replica, version=version if version else None)["bundle"]

        if not os.path.isdir(dest_name):
            os.makedirs(dest_name)

        for file_ in bundle["files"]:
            file_uuid = file_["uuid"]
            file_version = file_["version"]
            filename = file_.get("name", file_uuid)

            logger.info("File %s: Retrieving...", filename)
            file_path = os.path.join(dest_name, filename)

            # Attempt to download the data.  If a retryable exception occurs, we wait a bit and retry again.  The delay
            # increases each time we fail and decreases each time we successfully read a block.  We set a quota for the
            # number of failures that goes up with every successful block read and down with each failure.
            #
            # If we can, we will attempt HTTP resume.  However, we verify that the server supports HTTP resume.  If the
            # ranged get doesn't yield the correct header, then we start over.
            delay = min_delay_seconds
            retries_left = initial_retries_left
            hasher = hashlib.sha256()
            with open(file_path, "wb") as fh:
                while True:
                    try:
                        response = self.get_file._request(
                            dict(uuid=file_uuid, version=file_version, replica=replica),
                            stream=True,
                            headers={
                                'Range': "bytes={}-".format(fh.tell())
                            },
                        )
                        try:
                            if not response.ok:
                                logger.error("%s", "File {}: GET FAILED.".format(filename))
                                logger.error("%s", "Response: {}".format(response.text))
                                break

                            consume_bytes = int(fh.tell())
                            server_start = 0
                            content_range_header = response.headers.get('Content-Range', None)
                            if content_range_header is not None:
                                cre = re.compile("bytes (\d+)-(\d+)")
                                mo = cre.search(content_range_header)
                                if mo is not None:
                                    server_start = int(mo.group(1))

                            consume_bytes -= server_start
                            assert consume_bytes >= 0
                            if server_start > 0 and consume_bytes == 0:
                                logger.info("%s", "File {}: Resuming at {}.".format(
                                    filename, server_start))
                            elif consume_bytes > 0:
                                logger.info("%s", "File {}: Resuming at {}. Dropping {} bytes to match".format(
                                    filename, server_start, consume_bytes))

                                while consume_bytes > 0:
                                    bytes_to_read = min(consume_bytes, 1024*1024)
                                    content = response.iter_content(chunk_size=bytes_to_read)
                                    chunk = next(content)
                                    if chunk:
                                        consume_bytes -= len(chunk)

                            for chunk in response.iter_content(chunk_size=1024*1024):
                                if chunk:
                                    fh.write(chunk)
                                    hasher.update(chunk)
                                    retries_left = min(retries_left + 1, initial_retries_left)
                                    delay = max(delay / 2, min_delay_seconds)
                            break
                        finally:
                            response.close()
                    except (ChunkedEncodingError, ConnectionError, ReadTimeout):
                        if retries_left > 0:
                            # resume!!
                            logger.info("%s", "File {}: GET FAILED. Attempting to resume.".format(
                                filename, file_path))
                            time.sleep(delay)
                            delay *= 2
                            retries_left -= 1
                            continue
                        raise

                if hasher.hexdigest().lower() != file_["sha256"].lower():
                    os.remove(file_path)
                    logger.error("%s", "File {}: GET FAILED. Checksum mismatch.".format(filename))
                    raise ValueError("Expected sha256 {} Received sha256 {}".format(
                        file_["sha256"].lower(), hasher.hexdigest().lower()))
                else:
                    logger.info("%s", "File {}: GET SUCCEEDED. Stored at {}.".format(filename, file_path))

        return {}

    def upload(self, src_dir, replica, staging_bucket, timeout_seconds=1200):
        """
        Upload a directory of files from the local filesystem and create a bundle containing the uploaded files.

        This method requires the use of a client-controlled object storage bucket to stage the data for upload.
        """
        bundle_uuid = str(uuid.uuid4())
        files_to_upload, files_uploaded = [], []
        for filename in os.listdir(src_dir):
            full_file_name = os.path.join(src_dir, filename)
            files_to_upload.append(open(full_file_name, "rb"))

        logger.info("Uploading %i files from %s to %s", len(files_to_upload), src_dir, staging_bucket)
        file_uuids, uploaded_keys = upload_to_cloud(files_to_upload, staging_bucket=staging_bucket, replica=replica,
                                                    from_cloud=False)
        for file_handle in files_to_upload:
            file_handle.close()
        filenames = list(map(os.path.basename, uploaded_keys))
        filename_key_list = list(zip(filenames, file_uuids, uploaded_keys))

        for filename, file_uuid, key in filename_key_list:
            logger.info("File %s: registering...", filename)

            # Generating file data
            creator_uid = self.config.get("creator_uid", 0)
            source_url = "s3://{}/{}".format(staging_bucket, key)
            logger.info("File %s: registering from %s -> uuid %s", filename, source_url, file_uuid)

            response = self.put_file._request(dict(
                uuid=file_uuid,
                bundle_uuid=bundle_uuid,
                creator_uid=creator_uid,
                source_url=source_url
            ))
            version = response.json().get('version', "blank")
            files_uploaded.append(dict(name=filename, version=version, uuid=file_uuid, creator_uid=creator_uid))

            if response.status_code in (requests.codes.ok, requests.codes.created):
                logger.info("File %s: Sync copy -> %s", filename, version)
            else:
                assert response.status_code == requests.codes.accepted
                logger.info("File %s: Async copy -> %s", filename, version)

                timeout = time.time() + timeout_seconds
                wait = 1.0
                while time.time() < timeout:
                    try:
                        self.head_file(uuid=file_uuid, replica="aws", version=version)
                        break
                    except SwaggerAPIException as e:
                        if e.code != requests.codes.not_found:
                            msg = "File {}: Unexpected server response during registration"
                            raise RuntimeError(msg.format(filename))
                        time.sleep(wait)
                        wait = min(60.0, wait * self.UPLOAD_BACKOFF_FACTOR)
                else:
                    # timed out. :(
                    raise RuntimeError("File {}: registration FAILED".format(filename))
                logger.debug("Successfully uploaded file")

        file_args = [{'indexed': file_["name"].endswith(".json"),
                      'name': file_['name'],
                      'version': file_['version'],
                      'uuid': file_['uuid']} for file_ in files_uploaded]

        logger.info("%s", "Bundle {}: Registering...".format(bundle_uuid))

        response = self.put_bundle(uuid=bundle_uuid, replica=replica, creator_uid=creator_uid, files=file_args)
        logger.info("%s", "Bundle {}: Registered successfully".format(bundle_uuid))

        return {
            "bundle_uuid": bundle_uuid,
            "creator_uid": creator_uid,
            "replica": replica,
            "version": response["version"],
            "files": files_uploaded
        }
