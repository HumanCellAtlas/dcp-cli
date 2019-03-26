#!/usr/bin/env python

import os
import sys
import boto3
import json
import argparse


secret_client = boto3.client("secretsmanager")

def main(secret_name: str = None):
    secret_store = os.environ.get('DSS_SECRETS_STORE')
    test_stage = os.environ.get("DSS_TEST_STAGE")
    secret_value = secret_client.get_secret_value(SecretId=secret_name)
    print(secret_value)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--secret-name",
        required=True,
        help='the secret value that we would like to fetch'
    )
    args = parser.parse_args()
    main(secret_name=args.secret_name)



