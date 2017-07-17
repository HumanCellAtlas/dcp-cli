from ...added_command import AddedCommand

class PutFiles(AddedCommand):
    """Class containing info to reach the get endpoint of files."""

    @classmethod
    def _get_base_url(cls):
        return "https://hca-dss.czi.technology/v1"

    @classmethod
    def get_command_name(cls):
        return "put-files"

    @classmethod
    def _get_endpoint_info(cls):
        return {u'positional': [{u'description': u'A RFC4122-compliant ID for the bundle.', u'format': None, u'pattern': u'[A-Za-z0-9]{8}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{12}', u'required': True, u'argument': u'uuid', u'required_for': [u'/files/{uuid}'], u'type': u'string'}], u'seen': False, u'options': {u'version': {u'hierarchy': [u'version'], u'in': u'query', u'description': u'Timestamp of file creation in RFC3339.  If this is not provided, the latest version is returned.', u'required_for': [], u'format': u'date-time', u'pattern': None, u'array': False, u'required': False, u'type': u'string', u'metavar': None}, u'creator_uid': {u'hierarchy': [u'creator_uid'], u'in': u'body', u'description': u'User ID who is creating this file.', u'required_for': [u'/files/{uuid}'], u'format': u'int64', u'pattern': None, u'array': False, u'required': True, u'type': u'integer', u'metavar': None}, u'bundle_uuid': {u'hierarchy': [u'bundle_uuid'], u'in': u'body', u'description': u'A RFC4122-compliant ID for the bundle that contains this file.', u'required_for': [u'/files/{uuid}'], u'format': None, u'pattern': None, u'array': False, u'required': True, u'type': u'string', u'metavar': None}, u'source_url': {u'hierarchy': [u'source_url'], u'in': u'body', u'description': u'Cloud URL for source data.', u'required_for': [u'/files/{uuid}'], u'format': None, u'pattern': u'^(gs|s3|wasb)://', u'array': False, u'required': True, u'type': u'string', u'metavar': None}}, u'description': u'Create a new version of a file with a given UUID.  The file content is passed in through a cloud URL.  The file\non the cloud provider must have metadata set reflecting the file checksums and the file content type.\n\nThe metadata fields required are:\n- hca-dss-content-type: content-type of the file\n- hca-dss-sha256: SHA-256 checksum of the file\n- hca-dss-sha1: SHA-1 checksum of the file\n- hca-dss-s3_etag: S3 ETAG checksum of the file.  See\nhttps://stackoverflow.com/questions/12186993/what-is-the-algorithm-to-compute-the-amazon-s3-etag-for-a-file-larger-than-5gb\nfor the general algorithm for how checksum is calculated.  For files smaller than 64MB, this is the MD5 checksum\nof the file.  For files larger than 64MB but smaller than 640,000MB, we use 64MB chunks.  For files larger than\n640,000MB, we use a chunk size equal to the total file size divided by 10000, rounded up to the nearest MB.\nMB, in this section, refers to 1,048,576 bytes.  Note that 640,000MB is not the same as 640GB!\n- hca-dss-crc32c: CRC-32C checksum of the file\n'}