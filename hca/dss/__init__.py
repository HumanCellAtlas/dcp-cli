"""
Data Storage System
*******************
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import errno
import functools
import multiprocessing
from collections import defaultdict, namedtuple
import csv
import concurrent.futures
from datetime import datetime
from fnmatch import fnmatchcase
import hashlib
import os
import re
import time
import uuid
from io import open

import requests
from atomicwrites import atomic_write
from requests.exceptions import ChunkedEncodingError, ConnectionError, ReadTimeout

from hca.dss.util import iter_paths, object_name_builder, hardlink
from hca.util import USING_PYTHON2
from hca.util.compat import glob_escape
from ..util import SwaggerClient
from ..util.exceptions import SwaggerAPIException
from .. import logger
from .upload_to_cloud import upload_to_cloud


class DSSFile(namedtuple('DSSFile', ['name', 'uuid', 'version', 'sha256', 'size', 'indexed', 'replica'])):
    """
    Local representation of a file on the DSS
    """
    @classmethod
    def from_manifest_row(cls, row, replica):
        return cls(name=row['file_name'],
                   uuid=row['file_uuid'],
                   version=row['file_version'],
                   sha256=row['file_sha256'],
                   size=row['file_size'],
                   indexed=row['file_indexed'],
                   replica=replica)

    @classmethod
    def from_dss_bundle_response(cls, file_dict, replica):
        return cls(name=file_dict['name'],
                   uuid=file_dict['uuid'],
                   version=file_dict['version'],
                   sha256=file_dict['sha256'],
                   size=file_dict['size'],
                   indexed=file_dict['indexed'],
                   replica=replica)


class DSSClient(SwaggerClient):
    """
    Client for the Data Storage Service API.
    """
    UPLOAD_BACKOFF_FACTOR = 1.618
    # This variable is the configuration for download_manifest_v2. It specifies the length of the names of nested
    # directories for downloaded files.
    DIRECTORY_NAME_LENGTHS = [2, 4]
    threads = multiprocessing.cpu_count() * 5

    def __init__(self, *args, **kwargs):
        super(DSSClient, self).__init__(*args, **kwargs)
        self.commands += [self.download, self.download_manifest, self.download_manifest_v2, self.upload,
                          self.create_version]

    def _create_version(self):
        return datetime.utcnow().strftime("%Y-%m-%dT%H%M%S.%fZ")

    def create_version(self):
        """
            :param

            Prints a timestamp that can be used for versioning

        """
        print(self._create_version())

    def download(self, bundle_uuid, replica, version="", download_dir="",
                 metadata_files=('*',), data_files=('*',),
                 num_retries=10, min_delay_seconds=0.25):
        """
        Download a bundle and save it to the local filesystem as a directory.

        :param str bundle_uuid: The uuid of the bundle to download
        :param str replica: the replica to download from. The supported replicas are: `aws` for Amazon Web Services, and
            `gcp` for Google Cloud Platform. [aws, gcp]
        :param str version: The version to download, else if not specified, download the latest. The version is a
            timestamp of bundle creation in RFC3339
        :param str dest_name: The destination file path for the download
        :param iterable metadata_files: one or more shell patterns against which all metadata files in the bundle will be
            matched case-sensitively. A file is considered a metadata file if the `indexed` property in the manifest is
            set. If and only if a metadata file matches any of the patterns in `metadata_files` will it be downloaded.
        :param iterable data_files: one or more shell patterns against which all data files in the bundle will be matched
            case-sensitively. A file is considered a data file if the `indexed` property in the manifest is not set. The
            file will be downloaded only if a data file matches any of the patterns in `data_files` will it be
            downloaded.
        :param int num_retries: The initial quota of download failures to accept before exiting due to
            failures. The number of retries increase and decrease as file chucks succeed and fail.
        :param float min_delay_seconds: The minimum number of seconds to wait in between retries.

        Download a bundle and save it to the local filesystem as a directory.
        By default, all data and metadata files are downloaded. To disable the downloading of data files,
        use `--data-files ''` if using the CLI (or `data_files=()` if invoking `download` programmatically).
        Likewise for metadata files.

        If a retryable exception occurs, we wait a bit and retry again.  The delay increases each time we fail and
        decreases each time we successfully read a block.  We set a quota for the number of failures that goes up with
        every successful block read and down with each failure.
        """
        errors = 0

        with concurrent.futures.ThreadPoolExecutor(self.threads) as executor:
            futures_to_dss_file = {executor.submit(task): dss_file
                                   for dss_file, task in self._download_tasks(bundle_uuid,
                                                                              replica,
                                                                              version,
                                                                              download_dir,
                                                                              metadata_files,
                                                                              data_files,
                                                                              num_retries,
                                                                              min_delay_seconds)}
            for future in concurrent.futures.as_completed(futures_to_dss_file):
                dss_file = futures_to_dss_file[future]
                try:
                    future.result()
                except Exception as e:
                    errors += 1
                    logger.warning('Failed to download file %s version %s from replica %s',
                                   dss_file.uuid, dss_file.version, dss_file.replica, exc_info=e)
        if errors:
            raise RuntimeError('{} file(s) failed to download'.format(errors))

    def _download_tasks(self,
                        bundle_uuid,
                        replica,
                        version="",
                        download_dir="",
                        metadata_files=('*',),
                        data_files=('*',),
                        num_retries=10,
                        min_delay_seconds=0.25):
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
            dss_file = DSSFile.from_dss_bundle_response(file_, replica)
            filename = file_.get("name", dss_file.uuid)
            walking_dir = os.path.join(download_dir, bundle_uuid)

            globs = metadata_files if file_['indexed'] else data_files
            if not any(fnmatchcase(filename, glob) for glob in globs):
                continue

            intermediate_path, filename_base = os.path.split(filename)
            if intermediate_path:
                walking_dir = os.path.join(walking_dir, intermediate_path)
            if not os.path.isdir(walking_dir):
                os.makedirs(walking_dir)

            logger.info("File %s: Retrieving...", filename)
            file_path = os.path.join(walking_dir, filename_base)
            yield dss_file, functools.partial(self._download_and_link_to_filestore,
                                              download_dir,
                                              dss_file,
                                              file_path,
                                              num_retries=num_retries,
                                              min_delay_seconds=min_delay_seconds)

    def _download_and_link_to_filestore(self, download_dir, dss_file, file_path, num_retries, min_delay_seconds):
        file_store_path = self._download_to_filestore(download_dir,
                                                      dss_file,
                                                      num_retries=num_retries,
                                                      min_delay_seconds=min_delay_seconds)
        hardlink(file_store_path, file_path)

    def _download_to_filestore(self, download_dir, dss_file, num_retries=10, min_delay_seconds=0.25):
        """
        Attempt to download the data and save it in the 'filestore' location dictated by self._file_path()
        """
        dest_path = self._file_path(dss_file.sha256, download_dir)
        if os.path.exists(dest_path):
            logger.info("Skipping download of '%s' because it already exists at '%s'.", dss_file.name, dest_path)
        else:
            logger.debug("Downloading '%s' to '%s'.", dss_file.name, dest_path)
            self._download_file(dss_file, dest_path, num_retries=num_retries, min_delay_seconds=min_delay_seconds)
            logger.info("Download '%s' to '%s'.", dss_file.name, dest_path)
        return dest_path

    def _download_file(self, dss_file, dest_path, num_retries=10, min_delay_seconds=0.25):
        """
        Attempt to download the data.  If a retryable exception occurs, we wait a bit and retry again.  The delay
        increases each time we fail and decreases each time we successfully read a block.  We set a quota for the
        number of failures that goes up with every successful block read and down with each failure.

        If we can, we will attempt HTTP resume.  However, we verify that the server supports HTTP resume.  If the
        ranged get doesn't yield the correct header, then we start over.
        """
        directory, _ = os.path.split(dest_path)
        if directory:
            try:
                os.makedirs(directory)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
        with atomic_write(dest_path, mode="wb", overwrite=True) as fh:
            if dss_file.size == 0:
                return

            download_hash = self._do_download_file(dss_file, fh, num_retries, min_delay_seconds)

            if download_hash.lower() != dss_file.sha256.lower():
                # No need to delete what's been written. atomic_write ensures we're cleaned up
                logger.error("%s", "File {}: GET FAILED. Checksum mismatch.".format(dss_file.uuid))
                raise ValueError("Expected sha256 {} Received sha256 {}".format(
                    dss_file.sha256.lower(), download_hash.lower()))

    def _do_download_file(self, dss_file, fh, num_retries, min_delay_seconds):
        """
        Abstracts away complications for downloading a file, handles retries and delays, and computes its hash
        """
        hasher = hashlib.sha256()
        delay = min_delay_seconds
        retries_left = num_retries
        while True:
            try:
                response = self.get_file._request(
                    dict(uuid=dss_file.uuid, version=dss_file.version, replica=dss_file.replica),
                    stream=True,
                    headers={
                        'Range': "bytes={}-".format(fh.tell())
                    },
                )
                try:
                    if not response.ok:
                        logger.error("%s", "File {}: GET FAILED.".format(dss_file.uuid))
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
                            dss_file.uuid, server_start))
                    elif consume_bytes > 0:
                        logger.info("%s", "File {}: Resuming at {}. Dropping {} bytes to match".format(
                            dss_file.uuid, server_start, consume_bytes))

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
                            retries_left = min(retries_left + 1, num_retries)
                            delay = max(delay / 2, min_delay_seconds)
                    break
                finally:
                    response.close()
            except (ChunkedEncodingError, ConnectionError, ReadTimeout):
                if retries_left > 0:
                    logger.info("%s", "File {}: GET FAILED. Attempting to resume.".format(dss_file.uuid))
                    time.sleep(delay)
                    delay *= 2
                    retries_left -= 1
                    continue
                raise
        return hasher.hexdigest()

    @classmethod
    def _file_path(cls, checksum, download_dir):
        """
        returns a file's relative local path based on the nesting parameters and the files hash
        :param checksum: a string checksum
        :param download_dir: root directory for filestore
        :return: relative Path object
        """
        checksum = checksum.lower()
        file_prefix = '_'.join(['files'] + list(map(str, cls.DIRECTORY_NAME_LENGTHS)))
        path_pieces = [download_dir, '.hca', 'v2', file_prefix]
        checksum_index = 0
        assert(sum(cls.DIRECTORY_NAME_LENGTHS) <= len(checksum))
        for prefix_length in cls.DIRECTORY_NAME_LENGTHS:
            path_pieces.append(checksum[checksum_index:(checksum_index + prefix_length)])
            checksum_index += prefix_length
        path_pieces.append(checksum)
        return os.path.join(*path_pieces)

    @classmethod
    def _parse_manifest(cls, manifest):
        with open(manifest) as f:
            # unicode_literals is on so all strings are unicode. CSV wants a str so we need to jump through a hoop.
            delimiter = b'\t' if USING_PYTHON2 else '\t'
            reader = csv.DictReader(f, delimiter=delimiter, quoting=csv.QUOTE_NONE)
            return reader.fieldnames, list(reader)

    def _write_output_manifest(self, manifest, filestore_root):
        """
        Adds the file path column to the manifest and writes the copy to the current directory. If the original manifest
        is in the current directory it is overwritten with a warning.
        """
        output = os.path.basename(manifest)
        fieldnames, source_manifest = self._parse_manifest(manifest)
        if 'file_path' not in fieldnames:
            fieldnames.append('file_path')
        with atomic_write(output, overwrite=True) as f:
            delimiter = b'\t' if USING_PYTHON2 else '\t'
            writer = csv.DictWriter(f, fieldnames, delimiter=delimiter, quoting=csv.QUOTE_NONE)
            writer.writeheader()
            for row in source_manifest:
                row['file_path'] = self._file_path(row['file_sha256'], filestore_root)
                writer.writerow(row)
            if os.path.isfile(output):
                logger.warning('Overwriting manifest %s', output)
        logger.info('Rewrote manifest %s with additional column containing path to downloaded files.', output)

    def download_manifest_v2(self, manifest, replica,
                             num_retries=10,
                             min_delay_seconds=0.25,
                             download_dir='.'):
        """
        Process the given manifest file in TSV (tab-separated values) format and download the files referenced by it.
        The files are downloaded in the version 2 format.

        This download format will serve as the main storage format for downloaded files. If a user specifies a different
        format for download (coming in the future) the files will first be downloaded in this format, then hard-linked
        to the user's preferred format.

        :param str manifest: path to a TSV (tab-separated values) file listing files to download
        :param str replica: the replica to download from. The supported replicas are: `aws` for Amazon Web Services, and
            `gcp` for Google Cloud Platform. [aws, gcp]
        :param int num_retries: The initial quota of download failures to accept before exiting due to
            failures. The number of retries increase and decrease as file chucks succeed and fail.
        :param float min_delay_seconds: The minimum number of seconds to wait in between retries.

        Process the given manifest file in TSV (tab-separated values) format and download the files
        referenced by it.

        Each row in the manifest represents one file in DSS. The manifest must have a header row. The header row
        must declare the following columns:

        * `file_uuid` - the UUID of the file in DSS.

        * `file_version` - the version of the file in DSS.

        The TSV may have additional columns. Those columns will be ignored. The ordering of the columns is
        insignificant because the TSV is required to have a header row.
        """
        fieldnames, rows = self._parse_manifest(manifest)
        errors = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures_to_dss_file = {}
            for row in rows:
                dss_file = DSSFile.from_manifest_row(row, replica)
                future = executor.submit(self._download_to_filestore, download_dir, dss_file,
                                         num_retries=num_retries, min_delay_seconds=min_delay_seconds)
                futures_to_dss_file[future] = dss_file
            for future in concurrent.futures.as_completed(futures_to_dss_file):
                dss_file = futures_to_dss_file[future]
                try:
                    future.result()
                except Exception as e:
                    errors += 1
                    logger.warning('Failed to download file %s version %s from replica %s',
                                   dss_file.uuid, dss_file.version, dss_file.replica, exc_info=e)
        if errors:
            raise RuntimeError('{} file(s) failed to download'.format(errors))
        else:
            self._write_output_manifest(manifest, download_dir)

    def download_manifest(self, manifest, replica, num_retries=10, min_delay_seconds=0.25, download_dir=''):
        """
        Process the given manifest file in TSV (tab-separated values) format and download the files referenced by it.

        :param str manifest: path to a TSV (tab-separated values) file listing files to download
        :param str replica: the replica to download from. The supported replicas are: `aws` for Amazon Web Services, and
            `gcp` for Google Cloud Platform. [aws, gcp]
        :param int num_retries: The initial quota of download failures to accept before exiting due to
            failures. The number of retries increase and decrease as file chucks succeed and fail.
        :param float min_delay_seconds: The minimum number of seconds to wait in between retries.

        Process the given manifest file in TSV (tab-separated values) format and download the files
        referenced by it.

        Each row in the manifest represents one file in DSS. The manifest must have a header row. The header row
        must declare the following columns:

        * `bundle_uuid` - the UUID of the bundle containing the file in DSS.

        * `bundle_version` - the version of the bundle containing the file in DSS.

        * `file_name` - the name of the file as specified in the bundle.

        The TSV may have additional columns. Those columns will be ignored. The ordering of the columns is
        insignificant because the TSV is required to have a header row.
        """
        file_errors = 0
        file_task, bundle_errors = self._download_manifest_tasks(manifest,
                                                                 replica,
                                                                 num_retries,
                                                                 min_delay_seconds,
                                                                 download_dir)
        with concurrent.futures.ThreadPoolExecutor(self.threads) as executor:
            futures_to_dss_file = {executor.submit(task): dss_file
                                   for dss_file, task in file_task}
            for future in concurrent.futures.as_completed(futures_to_dss_file):
                dss_file = futures_to_dss_file[future]
                try:
                    future.result()
                except Exception as e:
                    file_errors += 1
                    logger.warning('Failed to download file %s version %s from replica %s',
                                   dss_file.uuid, dss_file.version, dss_file.replica, exc_info=e)
        if file_errors or bundle_errors:
            bundle_error_str = '{} bundle(s) failed to download'.format(bundle_errors) if bundle_errors else ''
            file_error_str = '{} file(s) failed to download'.format(file_errors) if file_errors else ''
            raise RuntimeError(bundle_error_str + (' and ' if bundle_errors and file_errors else '') + file_error_str)
        else:
            self._write_output_manifest(manifest, download_dir)
            logger.info('Primary copies of the files have been downloaded to `.hca` and linked '
                        'into per-bundle subdirectories of the current directory.')

    def _download_manifest_tasks(self, manifest, replica, num_retries, min_delay_seconds, download_dir):
        with open(manifest) as f:
            bundles = defaultdict(set)
            # unicode_literals is on so all strings are unicode. CSV wants a str so we need to jump through a hoop.
            delimiter = b'\t' if USING_PYTHON2 else '\t'
            reader = csv.DictReader(f, delimiter=delimiter, quoting=csv.QUOTE_NONE)
            for row in reader:
                bundles[(row['bundle_uuid'], row['bundle_version'])].add(row['file_name'])
        tasks = []
        errors = 0
        for (bundle_uuid, bundle_version), data_files in bundles.items():
            data_globs = tuple(glob_escape(file_name) for file_name in data_files if file_name)
            logger.info('Downloading bundle %s version %s ...', bundle_uuid, bundle_version)
            try:
                for task in self._download_tasks(bundle_uuid,
                                                 replica,
                                                 version=bundle_version,
                                                 download_dir=download_dir,
                                                 data_files=data_globs,
                                                 num_retries=num_retries,
                                                 min_delay_seconds=min_delay_seconds):
                    tasks.append(task)
            except Exception as e:
                errors += 1
                logger.warning('Bundle %s failed to download', bundle_uuid, exc_info=e)
        return tasks, errors

    def upload(self, src_dir, replica, staging_bucket, timeout_seconds=1200):
        """
        Upload a directory of files from the local filesystem and create a bundle containing the uploaded files.

        :param str src_dir: file path to a directory of files to upload to the replica.
        :param str replica: the replica to upload to. The supported replicas are: `aws` for Amazon Web Services, and
            `gcp` for Google Cloud Platform. [aws, gcp]
        :param str staging_bucket: a client controlled AWS S3 storage bucket to upload from.
        :param int timeout_seconds: the time to wait for a file to upload to replica.

        Upload a directory of files from the local filesystem and create a bundle containing the uploaded files.
        This method requires the use of a client-controlled object storage bucket to stage the data for upload.
        """
        bundle_uuid = str(uuid.uuid4())
        version = datetime.utcnow().strftime("%Y-%m-%dT%H%M%S.%fZ")

        files_to_upload, files_uploaded = [], []
        for filename in iter_paths(src_dir):
            full_file_name = filename.path
            files_to_upload.append(open(full_file_name, "rb"))

        logger.info("Uploading %i files from %s to %s", len(files_to_upload), src_dir, staging_bucket)
        file_uuids, uploaded_keys, abs_file_paths = upload_to_cloud(files_to_upload, staging_bucket=staging_bucket,
                                                                    replica=replica, from_cloud=False)
        for file_handle in files_to_upload:
            file_handle.close()
        filenames = [object_name_builder(p, src_dir) for p in abs_file_paths]
        filename_key_list = list(zip(filenames, file_uuids, uploaded_keys))

        for filename, file_uuid, key in filename_key_list:
            filename = filename.replace('\\', '/')  # for windows paths
            if filename.startswith('/'):
                filename = filename.lstrip('/')
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
                            req_id = 'X-AWS-REQUEST-ID: {}'.format(response.headers.get("X-AWS-REQUEST-ID"))
                            raise RuntimeError(msg.format(filename), req_id)
                        time.sleep(wait)
                        wait = min(60.0, wait * self.UPLOAD_BACKOFF_FACTOR)
                else:
                    # timed out. :(
                    req_id = 'X-AWS-REQUEST-ID: {}'.format(response.headers.get("X-AWS-REQUEST-ID"))
                    raise RuntimeError("File {}: registration FAILED".format(filename), req_id)
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
