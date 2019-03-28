#!/usr/bin/env python

import os
import boto3
import argparse
import codecs

secret_client = boto3.client("secretsmanager")


def main(secret_name: str = None):
    secret_store = os.environ.get('DSS_SECRETS_STORE')
    test_stage = os.environ.get("DSS_TEST_STAGE")
    secret_value = secret_client.get_secret_value(SecretId='{}/{}/{}'.format(secret_store, test_stage, secret_name))
    return secret_value["SecretString"]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--secret-name",
                        required=True,
                        help='the secret value that we would like to fetch'
                        )
    parser.add_argument("--write",
                        default=False,
                        action='store_true',
                        help='write to file, where filename is the secret_name parameter'
                        )
    args = parser.parse_args()
    secret_string = main(secret_name=args.secret_name)
    if args.write:
        with codecs.open(args.secret_name, 'w', encoding='utf-8') as f:
            f.write(secret_string)
    else:
        print(secret_string)
