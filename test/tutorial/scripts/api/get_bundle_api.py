import os
import json
import subprocess
from hca.dss import DSSClient

def main():
    dss = DSSClient()
    bundle = dss.get_bundle(
        replica="aws", uuid="002aeac5-4d74-462d-baea-88f5c620cb50", version="2019-08-01T200147.836900Z"
    )
    print_bundle(bundle)
    save_bundle(bundle)

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
    with open('data/get_bundle.json', 'w') as f:
        f.write(json.dumps(bundle))

if __name__=="__main__":
    main()
