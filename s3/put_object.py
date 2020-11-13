#!/usr/bin/env python

import boto
import boto.s3.connection

from boto.s3.key import Key

from sys import argv

from cred import *

from time import time

conn = boto.connect_s3(
        aws_access_key_id = S3_ACCESS_KEY,
        aws_secret_access_key = S3_SECRET_KEY,
        host = 'HOSTNAME',
        port = 443,
        is_secure=True,               # uncomment if you are not using ssl
        calling_format = boto.s3.connection.OrdinaryCallingFormat(),
        )

bucket_name = argv[1]
key_string = argv[2]

b = conn.get_bucket(bucket_name)
k = Key(b)
k.key = key_string

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

file_name = argv[3]
with open(file_name,'r') as f:
        k.compute_md5(f)

#sum = 'ae5a572dd92448821a3cfb22b03dd323'
#sum2ple = k.get_md5_from_hexdigest(sum)
t0=time()
k.set_contents_from_filename(file_name, cb=progress, num_cb=10)
