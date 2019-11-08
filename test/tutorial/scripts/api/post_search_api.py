from hca.dss import DSSClient

dss = DSSClient()

# Note:
# Passing es_query={} runs an empty search, which will match all bundles.

# Iterable post_search
for results in dss.post_search.iterate(replica="aws", es_query={}):
    print(results)
    break

# Non-iterable (first page only) post_search
print(dss.post_search(replica='aws', es_query={}))
