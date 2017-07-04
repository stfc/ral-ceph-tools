#!/usr/bin/env python

import boto
import boto.s3.connection

from boto.s3.key import Key

from sys import argv

from cred import *

from time import time

def progress(transferred, total):
    pct = float(transferred)/total
    tt = time() - t0
    rate = transferred / tt
    for p in ['B','KB','MB','GB','TB']:
      if rate/1024 > 1:
        rate = rate / 1024
      else:
        break
    print "{percentage:.0%} done. {rate:.2f} {unit}/sec".format(percentage=pct, rate=rate, unit=p)

conn = boto.connect_s3(
        aws_access_key_id = S3_ACCESS_KEY,
        aws_secret_access_key = S3_SECRET_KEY,
        host = 'localhost',
        port = 443,
        is_secure=True,               # uncomment if you are not using ssl
        calling_format = boto.s3.connection.OrdinaryCallingFormat(),
        )

bucket_name = argv[1]

thebucket = conn.get_bucket(bucket_name)

key = argv[2]

k = Key(thebucket)

k.key = key

file_name = argv[3]

t0 = time()
k.get_contents_to_filename(file_name, cb=progress, num_cb=10)

print k.md5
