from hca.dss import DSSClient

dss = DSSClient()

# Iterates through bundles.
for results in dss.post_search.iterate(replica="aws", es_query={}):
    print(results)
    break

# Outputs the first page of bundles.
print(dss.post_search(replica='aws', es_query={}))
