import os
import sys
import boto3
import json
import argparse


secret_client = boto3.client("secretsmanager")




if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--secrets-name",
        default=None,
        required=True,
        help='the secret value that we would like to fetch'
    )
    args = parser.parse_args()

secret_store = os.environ.get('DSS_SECRETS_STORE')
test_stage = os.environ.get("DSS_TEST_STAGE")
secret_name = args.secrets_name
secret_client.get_secret_value(SecretId=secret_name)


