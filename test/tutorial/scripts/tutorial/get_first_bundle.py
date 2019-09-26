from hca import HCAConfig
from hca.dss import DSSClient

hca_config = HCAConfig()
hca_config['DSSClient'].swagger_url = f'https://dss.dev.data.humancellatlas.org/v1/swagger.json'
dss = DSSClient(config=hca_config)
for i in dss.post_search.iterate(replica='aws', es_query={}):
    uuid, version = i['bundle_fqid'].split('.', 1)
    try:
        s = f'Bundle: {uuid}.{version}\n'
        for j in dss.get_bundle(replica='aws', uuid=uuid, version=version)['bundle']['files']:
            file_version = j['version']
            file_uuid = j['uuid']
            s += f'    File: {file_uuid}.{file_version}\n'
        print(s[:-1])
        break
    except:
        pass  # print(f'Does not exist: {uuid}.{version}')