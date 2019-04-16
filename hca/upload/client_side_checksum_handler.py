import os
import time

from dcplib.checksumming_io import ChecksummingSink
from dcplib.s3_multipart import get_s3_multipart_chunk_size

# Checksum(s) to compute for file; current options: crc32c, sha1, sha256, s3_etag
CHECKSUM_NAMES = ['crc32c']


class ClientSideChecksumHandler:
    """ The ClientSideChecksumHandler takes in a file as a parameter and handles any behavior related to
    check-summing the file
    on the client-side, returning a tag that can be used as metadata when the file is uploaded to S3."""

    def __init__(self, filename):
        self._checksums = {}
        self._filename = filename

    def get_checksum_metadata_tag(self):
        """ Returns a map of checksum values by the name of the hashing function that produced it."""
        if not self._checksums:
            print("Warning: No checksums have been computed for this file.")
        return {str(_hash_name): str(_hash_value) for _hash_name, _hash_value in self._checksums.items()}

    def compute_checksum(self):
        """ Calculates checksums for a given file. """
        if self._filename.startswith("s3://"):
            print("Warning: Did not perform client-side checksumming for file in S3. To be implemented.")
            pass
        else:
            checksumCalculator = self.ChecksumCalculator(self._filename)
            self._checksums = checksumCalculator.compute()

    class ChecksumCalculator:
        """ The ChecksumCalculator encapsulates calling various library functions based on the required checksum to
        be calculated on a file."""

        def __init__(self, filename, checksums=CHECKSUM_NAMES):
            self._filename = filename
            self._checksums = checksums

        def compute(self):
            """ Compute the checksum(s) for the given file and return a map of the value by the hash function name. """
            start_time = time.time()
            _file_size = os.path.getsize(self._filename)
            _multipart_chunksize = get_s3_multipart_chunk_size(_file_size)
            with ChecksummingSink(_multipart_chunksize, hash_functions=self._checksums) as sink:
                with open(self._filename, 'rb') as _file_object:
                    sink.write(_file_object.read())
                    checksums = sink.get_checksums()
                    print("Checksumming took %.2f milliseconds to compute" % ((time.time() - start_time) * 1000))
            return checksums
