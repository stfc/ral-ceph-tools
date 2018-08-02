#!/usr/bin/env python

import boto
import boto.s3.connection

from sys import argv

from cred import *

conn = boto.connect_s3(
        aws_access_key_id = S3_ACCESS_KEY,
        aws_secret_access_key = S3_SECRET_KEY,
        host = 'echo.stfc.ac.uk',
        port = 443,
        #is_secure=False,               # uncomment if you are not using ssl
        calling_format = boto.s3.connection.OrdinaryCallingFormat(),
        )

bucket_name = argv[1]
# The external server is normally the dynafed alias
external_server = argv[2]

cors_rule = {
    "CORSRules": [
        {
            "AllowedMethods": ["GET", "PUT"],
            "AllowedOrigins": [external_server],
            "MaxAgeSeconds": 3000
        }
    ]
}

s3_client.put_bucket_cors(Bucket=bucket, CORSConfiguration=cors_rule)
