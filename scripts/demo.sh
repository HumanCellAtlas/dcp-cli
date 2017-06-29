#!/bin/bash

# This is a demo script to present the basic end-to-end data flow between the core HCA DCP systems, as seen from the client
# side. It's a work in progress, and will be expanded over time to incorporate evolving design, operations, API and CLI
# details.

set -euo pipefail

# ./mock-ingest-api

for bundle in ~/projects/data-bundle-examples/smartseq2/*; do
    hca upload $bundle > ${bundle}_uploaded.json
done

d(){

bundle_manifest=$(hca upload $bundle)
bundle_uuid=$(echo "$bundle_manifest" | jq .bundle_uuid)

# Or, manually:
# aws s3 sync $bundle s3://hca-dcp-staging-dev/$bundle
# for file in $(jq "$bundle/manifest.json" .files[]); do
#     hca put-file $file
# done
# hca put-bundles $bundle

# Show reading back bundles and files with and without versions from both replicas (demos the sync engine)
hca download --name test_demo $bundle_uuid

# hca get-bundles --replica gcs UUID
# hca get-bundles --replica aws UUID
# hca get-files --replica gce UUID ...
# Update a file in a downloaded bundle, upload it as a new version,
# and see that the file and bundle versions changed

cat test_demo/sample.json test_demo/sample.json > test_demo/sample.json
hca upload test_demo/sample.json --uuid EXISTING FILE UUID FROM $bundle_manifest
export new_file_manifest=$(hca get-files EXISTING FILE UUID FROM $bundle_manifest)
new_bundle_manifest=$(echo "$bundle_manifest" | jq .files...=env.new_file_manifest)
hca put-bundles $bundle_uuid $new_bundle_manifest

# New bundle manifest for the latest version reflects updated sample.json
hca get-bundles $bundle_uuid

# Show querying of bundles and files through /search
http https://hca-dss.czi.technology/v1/search query=='{"foo": "bar"}'
}

hca post-search --query="$(cat ~/projects/data-store/tests/sample_query.json)"

d2(){
# Show creating a stored search (webhook subscription)
# Fire off a mock event to the green box
# (Either the green box pipeline runs, or we mock it)
http POST https://green-dot-broad-dsde-mint-dev.appspot.com/v1/notifications example_webhook_payload.json
#   - Green box accesses bundles, files, and possibly runs queries
# Another round of put-file/put-bundle for a secondary analysis result
}
