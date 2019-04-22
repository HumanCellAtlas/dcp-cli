import requests
import os
import argparse
import json


ec2_auth_url = 'http://169.254.169.254/latest/meta-data/iam/security-credentials/'

credential_string = """[default]
aws_access_key_id = {}
aws_secret_access_key = {}
token = {}
"""

config_string = """[default]
region = {}

"""


def get_default_aws_folder():
    if os.name is 'nt':
        return "%UserProfile%\.aws"
    else:
        return "~/.aws"


def get_ec2_security_credentials(role_name):
    ec2_auth_url_role = ec2_auth_url + role_name
    res = requests.get(ec2_auth_url_role)
    return json.dumps(res.json())


def write_string_to_file(path_to_file, string_to_write):
    print("attempting to modify: {}".format(path_to_file))
    with open(path_to_file, "w") as file:
        file.write(string_to_write)
        file.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--role-name",
                        required=True,
                        help='the iam role that is attached for the runner ec2 instance'
                        )
    parser.add_argument("--region-name",
                        required=True,
                        help='the default region for the iam-role'
                        )
    parser.add_argument("--write",
                        default=False,
                        action='store_true',
                        help='writes to shared credential file'
                        )
    args = parser.parse_args()
    security_credentials = get_ec2_security_credentials(args.role_name)
    if args.write:
        config_path = os.path.join(get_default_aws_folder(), "config")
        credential_path = os.path.join(get_default_aws_folder(), "credentials")
        write_string_to_file(config_path, config_string.format(args.region_name))
        write_string_to_file(credential_path, credential_string.format(security_credentials['AccessKeyID'],
                                                                       security_credentials['SecretAccessKey'],
                                                                       security_credentials['Token']))
    else:
        print(security_credentials)
