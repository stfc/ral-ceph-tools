#!/usr/bin/env python

from datetime import datetime
from socket import gethostname
from json import loads
from socket import gethostname
from boto.s3.key import Key

import subprocess
import ssl
import boto
import boto.s3.connection

# Site specific settings
USER = "atlas"
HOST = "s3.echo.stfc.ac.uk"
PORT = "443"
SSL = True

client_name = '.'.join(['client','rgw',gethostname().split('.')[0]])
cmd = ['radosgw-admin', '-n', client_name, 'user', 'info', '--uid', USER]
p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
ui = p.communicate()[0]
uid = loads(ui)

AWS_ACCESS_KEY = uid['keys'][0]['access_key']
AWS_SECRET_KEY = uid['keys'][0]['secret_key']

BUCKET_NAME = config['bucket']


## Connect to the gateway
# try:
ssl._https_verify_certificates(False)
connection = boto.connect_s3(
    aws_access_key_id = AWS_ACCESS_KEY,
    aws_secret_access_key = AWS_SECRET_KEY,
    host = HOST,
    port = PORT,
    is_secure = SSL,
    calling_format = boto.s3.connection.OrdinaryCallingFormat()
)

try:
    bucket = connection.get_bucket(BUCKET_NAME)
except:
    # handle bucket errors here

key = Key(bucket)
key.key = # name you want the object to have in the bucket

data = # textual data will work fine (e.g. JSON output from json.puts)

## Write it
try:
    key.set_contents_from_string(data)
except:
    # handle errors
