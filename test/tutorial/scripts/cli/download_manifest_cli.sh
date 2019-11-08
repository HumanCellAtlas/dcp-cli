#!/usr/bin/env bash

MANIFEST="manifest.tsv"

# Make the manifest file
cat /dev/null > ${MANIFEST}
echo -e "bundle_uuid\tbundle_version\tfile_name\tfile_uuid\tfile_version\tfile_sha256\tfile_size\tfile_path\n" >> ${MANIFEST}
echo -e "ffffaf55-f19c-40e3-aa81-a6c69d357265\t2019-08-01T200147.836832Z\tlinks.json\tdbf7bd27-b58e-431d-ba05-6a48f29e7cef\t2019-08-03T150636.118831Z\tda4df14eb39cacdff01a08f27685534822c2d40adf534ea7b3e4adf261b9079a\t2081\t.hca/v2/files_2_4/da/4df1/da4df14eb39cacdff01a08f27685534822c2d40adf534ea7b3e4adf261b9079a\n" >> ${MANIFEST}

echo "manifest.json file: ${MANIFEST}"

# Download files in the manifest
hca dss download-manifest --replica aws --manifest ${MANIFEST}
