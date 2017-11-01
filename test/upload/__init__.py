import base64
import json
import os
import uuid

import tweak

import hca
from hca.upload import UploadArea, UploadAreaURN

UPLOAD_BUCKET_NAME_TEMPLATE = 'bogo-bucket-{deployment_stage}'
TEST_UPLOAD_BUCKET = UPLOAD_BUCKET_NAME_TEMPLATE.format(deployment_stage=os.environ['DEPLOYMENT_STAGE'])


def setup_tweak_config():
    config = tweak.Config(hca.TWEAK_PROJECT_NAME)
    config.upload = {
        'areas': {},
        'bucket_name_template': UPLOAD_BUCKET_NAME_TEMPLATE
    }
    config.save()


def mock_current_upload_area():
    area = mock_upload_area()
    area.select()
    return area


def mock_upload_area(area_uuid=None):
    """
    Create a UUID and URN for a fake upload area, store it in Tweak config.
    """
    stage = os.environ['DEPLOYMENT_STAGE']
    if not area_uuid:
        area_uuid = str(uuid.uuid4())
    creds = {'AWS_ACCESS_KEY_ID': 'foo', 'AWS_SECRET_ACCESS_KEY': 'bar'}
    encoded_creds = base64.b64encode(json.dumps(creds).encode('ascii')).decode('ascii')
    urn = "dcp:upl:aws:{}:{}:{}".format(stage, area_uuid, encoded_creds)
    area = UploadArea(urn=UploadAreaURN(urn))
    return area
