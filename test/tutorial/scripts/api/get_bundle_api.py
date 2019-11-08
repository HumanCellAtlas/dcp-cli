import os
import json
import subprocess
from hca.dss import DSSClient

BUNDLE_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'get_bundle.json')

def main():
    bundle = fetch_bundle()
    print_bundle(bundle)
    save_bundle(bundle)

def fetch_bundle():
    dss = DSSClient()
    return dss.get_bundle(
        replica="aws", uuid="002aeac5-4d74-462d-baea-88f5c620cb50", version="2019-08-01T200147.836900Z"
    )

def print_bundle(bundle):
    """Print a bundle and its contents to the console"""
    print("Bundle Contents:")
    for file in bundle["bundle"]["files"]:
        print(f"File: {json.dumps(file, indent=4)}")
    
    print(f'Bundle Creator: {bundle["bundle"]["creator_uid"]}')
    print(f'Bundle UUID   : {bundle["bundle"]["uuid"]}')
    print(f'Bundle Version: {bundle["bundle"]["version"]}')

def save_bundle(bundle):
    """Save bundle information to a JSON file. Useful for download_manifest_api.py script."""
    if not os.path.exists("data"):
        subprocess.call(["mkdir", "data"])
    with open(BUNDLE_JSON, 'w') as f:
        f.write(json.dumps(bundle))

if __name__=="__main__":
    main()
