#!/usr/bin/env bash

# Creates a sub based given a replica and a url
instance_info=$(hca dss put-subscription --callback-url https://dcp-cli-tutorials-put-get-delete-sub.com --replica aws) 

ID=`echo ${instance_info} | jq -r '.uuid'`

echo $ID

# Lists all of subs created
hca dss get-subscriptions --replica aws

# List a sub
hca dss get-subscription --replica aws --uuid $ID

# Deletes a sub based on a UUID
hca dss delete-subscription --replica aws --uuid $ID
