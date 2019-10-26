#!/usr/bin/env bash

# Get the latest version
hca dss head-file \
    --replica aws \
    --uuid 666ff3f0-67a1-4ead-82e9-3f96a8c0a9b1

# Get the specified version
hca dss head-file \
    --replica aws \
    --uuid 6887bd52-8bea-47d9-bbd9-ff71e05faeee \
    --version 2019-01-30T165057.189000Z
