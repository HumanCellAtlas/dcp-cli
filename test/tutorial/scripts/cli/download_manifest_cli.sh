#!/usr/bin/env bash

MANIFEST="manifest.tsv"

# Make the manifest file
cat /dev/null > ${MANIFEST}
echo "bundle_uuid	bundle_version	file_name	file_uuid	file_version	file_sha256	file_size	file_path" >> ${MANIFEST}
echo "ffffaf55-f19c-40e3-aa81-a6c69d357265	2019-08-01T200147.836832Z	links.json dbf7bd27-b58e-431d-ba05-6a48f29e7cef	2019-08-03T150636.118831Z da4df14eb39cacdff01a08f27685534822c2d40adf534ea7b3e4adf261b9079a	2081 .hca/v2/files_2_4/da/4df1/da4df14eb39cacdff01a08f27685534822c2d40adf534ea7b3e4adf261b9079a" >> ${MANIFEST}

# Download files in the manifest
hca dss download-manifest \
    --replica aws \
    --manifest ${MANIFEST}
