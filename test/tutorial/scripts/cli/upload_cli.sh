#!/usr/bin/env bash

hca dss upload \
    --src-dir data/ \
    --replica aws \
    --staging-bucket upload-test-unittest

aws s3 rm s3://upload-test-unittest --recursive
