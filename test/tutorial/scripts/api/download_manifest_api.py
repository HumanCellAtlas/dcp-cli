from hca import HCAConfig
from hca.dss import DSSClient
import csv
import json
import pprint

hca_config = HCAConfig()
hca_config["DSSClient"].swagger_url = f"https://dss.data.humancellatlas.org/v1/swagger.json"
dss = DSSClient(config=hca_config)

with open("manifest.tsv", "w") as manifest:
    tsv = csv.DictWriter(
        manifest,
        fieldnames=(
            "bundle_uuid",
            "bundle_version",
            "file_name",
            "file_uuid",
            "file_version",
            "file_sha256",
            "file_size",
        ),
        delimiter="\t",
        quoting=csv.QUOTE_NONE,
    )
    tsv.writeheader()

    with open("./data/get_bundle.json") as jsonfile:
        try:
            data = json.load(jsonfile)
            bundle_uuid, bundle_version = data["bundle"]["uuid"], data["bundle"]["version"]
            pprint.pprint(data)
            for content in data["bundle"]["files"]:
                if content['name'].endswith('.json'):
                    tsv.writerow(
                            dict(
                                bundle_uuid=bundle_uuid,
                                bundle_version=bundle_version,
                                file_name=content["name"],
                                file_uuid=content["uuid"],
                                file_version=content["version"],
                                file_sha256=content["sha256"],
                                file_size=content["size"],
                            )
                        )
        except ValueError as e:
            print('Not JSON FILE %s' % e)
            pass

dss.download_manifest(replica="aws", manifest="manifest.tsv")
