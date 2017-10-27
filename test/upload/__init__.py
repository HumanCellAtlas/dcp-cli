import os

UPLOAD_BUCKET_NAME_TEMPLATE = 'bogo-bucket-{deployment_stage}'
TEST_UPLOAD_BUCKET = UPLOAD_BUCKET_NAME_TEMPLATE.format(deployment_stage=os.environ['DEPLOYMENT_STAGE'])
