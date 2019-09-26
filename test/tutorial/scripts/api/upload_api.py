from hca import HCAConfig
from hca.dss import DSSClient
import boto3    

s3 = boto3.resource('s3')
bucket = s3.Bucket('upload-test-unittest') 

hca_config = HCAConfig()
hca_config["DSSClient"].swagger_url = f"https://dss.dev.data.humancellatlas.org/v1/swagger.json"
dss = DSSClient(config=hca_config)

print(dss.upload(src_dir="data/", replica="aws", staging_bucket="upload-test-unittest"))
 
bucket.objects.all().delete()

print("Upload successful")
