from __future__ import absolute_import, division, print_function, unicode_literals

from collections import defaultdict
import csv
from datetime import datetime
from fnmatch import fnmatchcase
import hashlib
import os
import re
import time
import uuid
from io import open

import requests
from requests.exceptions import ChunkedEncodingError, ConnectionError, ReadTimeout

from hca.util import USING_PYTHON2
from hca.util.compat import glob_escape
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
        self.commands += [self.download, self.download_manifest, self.upload]

    def download(self, bundle_uuid, replica, version="", dest_name="",
                 metadata_files=('*',), data_files=('*',),
                 initial_retries_left=10, min_delay_seconds=0.25):
        """
        Download a bundle and save it to the local filesystem as a directory.

        `metadata_files` (`--metadata-files` on the CLI) are one or more shell patterns against which all metadata
        files in the bundle will be matched case-sensitively. A file is considered a metadata file if the `indexed`
        property in the manifest is set. If and only if a metadata file matches any of the patterns in
        `metadata_files` will it be downloaded.

        `data_files` (`--data-files` on the CLI) are one or more shell patterns against which all data files in the
        bundle will be matched case-sensitively. A file is considered a data file if the `indexed` property in the
        manifest is not set. If and only if a data file matches any of the patterns in `data_files` will it be
        downloaded.

        By default, all data and metadata files are downloaded. To disable the downloading of data files,
        use `--data-files ''` if using the CLI (or `data_files=()` if invoking `download` programmatically). Likewise
        for metadata files.
        """
        if not dest_name:
            dest_name = bundle_uuid

        bundle = self.get_bundle(uuid=bundle_uuid, replica=replica, version=version if version else None)["bundle"]

        files = {}
        for file_ in bundle["files"]:
            # The file name collision check is case-insensitive even if the local file system we're running on is
            # case-sensitive. We do this in order to get consistent download behavior on all operating systems and
            # file systems. The case of file names downloaded to a case-sensitive system will still match exactly
            # what's specified in the bundle manifest. We just don't want a bundle with files 'Foo' and 'foo' to
            # create two files on one system and one file on the other. Allowing this to happen would, in the best
            # case, overwrite Foo with foo locally. A resumed download could produce a local file called foo that
            # contains a mix of data from Foo and foo.
            filename = file_.get("name", file_["uuid"]).lower()
            if files.setdefault(filename, file_) is not file_:
                raise ValueError("Bundle {bundle_uuid} version {bundle_version} contains multiple files named "
                                 "'{filename}' or a case derivation thereof".format(filename=filename, **bundle))

        for file_ in files.values():
            file_uuid = file_["uuid"]
            file_version = file_["version"]
            filename = file_.get("name", file_uuid)

            globs = metadata_files if file_['indexed'] else data_files
            if not any(fnmatchcase(filename, glob) for glob in globs):
                continue

            if not os.path.isdir(dest_name):
                os.makedirs(dest_name)

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

    def download_manifest(self, manifest, replica, initial_retries_left=10, min_delay_seconds=0.25):
        """
        Process the given manifest file in TSV (tab-separated values) format and download the files referenced by it.

        Each row in the manifest represents one file in DSS. The manifest must have a header row. The header row must
        declare the following columns:

        `bundle_uuid` - the UUID of the bundle containing the file in DSS

        `bundle_version` - the version of the bundle containing the file in DSS

        `file_name` - the name of the file as specified in the bundle

        The TSV may have additional columns. Those columns will be ignored. The ordering of the columns is
        insignificant because the TSV is required to have a header row.
        """
        with open(manifest) as f:
            bundles = defaultdict(set)
            # unicode_literals is on so all strings are unicode. CSV wants a str so we need to jump through a hoop.
            delimiter = '\t'.encode('ascii') if USING_PYTHON2 else '\t'
            reader = csv.DictReader(f, delimiter=delimiter, quoting=csv.QUOTE_NONE)
            for row in reader:
                bundles[(row['bundle_uuid'], row['bundle_version'])].add(row['file_name'])
        errors = 0
        for (bundle_uuid, bundle_version), data_files in bundles.items():
            data_globs = tuple(glob_escape(file_name) for file_name in data_files if file_name)
            logger.info('Downloading bundle %s version %s ...', bundle_uuid, bundle_version)
            try:
                self.download(bundle_uuid,
                              replica,
                              version=bundle_version,
                              data_files=data_globs,
                              initial_retries_left=initial_retries_left,
                              min_delay_seconds=min_delay_seconds)
            except Exception as e:
                errors += 1
                logger.warning('Failed to download bundle %s version %s from replica %s',
                               bundle_uuid, bundle_version, replica, exc_info=e)
        if errors:
            raise RuntimeError('{} bundle(s) failed to download'.format(errors))
        else:
            return {}

    def upload(self, src_dir, replica, staging_bucket, timeout_seconds=1200):
        """
        Upload a directory of files from the local filesystem and create a bundle containing the uploaded files.

        This method requires the use of a client-controlled object storage bucket to stage the data for upload.
        """
        bundle_uuid = str(uuid.uuid4())
        version = datetime.utcnow().strftime("%Y-%m-%dT%H%M%S.%fZ")

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
                version=version,
                creator_uid=creator_uid,
                source_url=source_url
            ))
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

        response = self.put_bundle(uuid=bundle_uuid,
                                   version=version,
                                   replica=replica,
                                   creator_uid=creator_uid,
                                   files=file_args)
        logger.info("%s", "Bundle {}: Registered successfully".format(bundle_uuid))

        return {
            "bundle_uuid": bundle_uuid,
            "creator_uid": creator_uid,
            "replica": replica,
            "version": response["version"],
            "files": files_uploaded
        }
