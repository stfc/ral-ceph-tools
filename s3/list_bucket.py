#!/usr/bin/env python

import boto
import boto.s3.connection
from cred import *

conn = boto.connect_s3(
        aws_access_key_id = S3_ACCESS_KEY,
        aws_secret_access_key = S3_SECRET_KEY,
        host = 'ceph-gw4.gridpp.rl.ac.uk',
        port = 443,
        is_secure=True,               # uncomment if you are not using ssl
        calling_format = boto.s3.connection.OrdinaryCallingFormat(),
        )
for bucket in conn.get_all_buckets():
        print "{name}\t{created}".format(
                name = bucket.name,
                created = bucket.creation_date,
        )
