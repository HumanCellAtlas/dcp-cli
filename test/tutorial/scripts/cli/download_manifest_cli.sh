#!/usr/bin/env bash

touch manifest.tsv

echo "bundle_uuid	bundle_version	file_name	file_uuid	file_version	file_sha256	file_size	file_path" >> ./manifest.tsv

hca dss download-manifest --replica aws --manifest manifest.tsv