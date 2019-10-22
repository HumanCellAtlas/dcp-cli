from hca.dss import DSSClient

dss = DSSClient()

print("Calling dss.head_file() with a file UUID:")
response = dss.head_file(
    uuid="6887bd52-8bea-47d9-bbd9-ff71e05faeee",
    replica="aws",
)
if response.status_code==200:
    print("Success!")
    print("Headers: %s"%(response.headers))

print()

# Optionally, add a version
print("Calling dss.head_file() with a file UUID and version:")
response = dss.head_file(
    uuid="6887bd52-8bea-47d9-bbd9-ff71e05faeee",
    replica="aws",
    version="2019-01-30T165057.189000Z",
)
if response.status_code==200:
    print("Success!")
    print("Headers: %s"%(response.headers))
