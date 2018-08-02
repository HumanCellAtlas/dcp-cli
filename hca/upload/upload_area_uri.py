from six.moves.urllib.parse import urlparse


class UploadAreaURI:

    """
    Upload area URIs take the form s3://<upload-bucket-prefix>-<deployment_stage>/<area_uuid>/

    e.g. s3://org-humancellatlas-upload-prod/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/
    """

    def __init__(self, uri):
        self.uri = uri
        self.parsed = urlparse(self.uri)

    def __str__(self):
        return self.uri

    @property
    def bucket_name(self):
        return self.parsed.netloc

    @property
    def deployment_stage(self):
        return self.bucket_name.split('-')[-1]

    @property
    def area_uuid(self):
        return self.parsed.path.split('/')[-2]
