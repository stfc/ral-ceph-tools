#!/usr/bin/env python

import subprocess, json, ssl, boto
import boto.s3.connection
from time import time
from boto.s3.key import Key

## Site specific settings
# Name of the atlas account
USER = "atlas"
# Host and port to contact when uploading josn file
HOST = "s3.echo.stfc.ac.uk"
PORT = 443
# For https SSL = True
SSL = True
# List of buckets to provide space reporting for
BUCKETS = ['atlas-eventservice','atlas-logs']
# Target bucket to upload the space-usage.json too
JSONDST = 'atlas-eventservice'

# Get bucket info
cmd = ['radosgw-admin', 'bucket', 'stats', '--uid', USER]
p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
ui = p.communicate()[0]
uid = json.loads(ui)

# Create dictionary
data = {}
for entry in uid:
    if entry['bucket'] in BUCKETS:
        USAGE = entry['usage']['rgw.main']['size']
        FILES = entry['usage']['rgw.main']['num_objects']
        QUOTA = entry['bucket_quota']['max_size']
        PATHS = "/" + entry['bucket'] + '/'
        data[entry['bucket']] = {'status': 'online', 'status_message': 'Report for space on RAL OS', 'list_of_paths': [PATHS], 'total_space': QUOTA, 'used_space': USAGE, 'num_files': FILES, 'time_stamp':  time()}

# Write the output to a .json file
tmpFile = '/tmp/space-usage.json'
with open(tmpFile, 'w') as outfile:
  json.dump(data, outfile)


# Run the Radosgw-admin command to retrieve the quota S3 credentials to upload json file to bucket.
cmd = ['radosgw-admin', 'user', 'info', '--uid', USER]
p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
ui = p.communicate()[0]
uid = json.loads(ui)
S3_ACCESS_KEY = uid['keys'][0]['access_key']
S3_SECRET_KEY = uid['keys'][0]['secret_key']

ssl._https_verify_certificates(False)
conn = boto.connect_s3(
        aws_access_key_id = S3_ACCESS_KEY,
        aws_secret_access_key = S3_SECRET_KEY,
        host = HOST,
        port = PORT,
        is_secure=SSL,
        calling_format = boto.s3.connection.OrdinaryCallingFormat(),
        )

b = conn.get_bucket(JSONDST)
k = Key(b)
k.key = 'space-usage.json'
k.set_contents_from_filename(tmpFile)
