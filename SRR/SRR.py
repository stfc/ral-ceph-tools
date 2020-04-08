#!/usr/bin/env python

import json, jinja2, subprocess, time, boto, boto.s3.connection
from boto.s3.key import Key
from datetime import date

def main():
  templateFilePath = jinja2.FileSystemLoader('./')
  env = jinja2.Environment(loader=templateFilePath)
  template = env.get_template('example.json')

  config = {}
  config['version'] = get_version()
  config['timestamp'] = get_time()
  config.update(get_total_usage())
  config['alice'] = {'quota' : 1320000000000000, 'used' : get_usage('alice')}
  config['atlas'] = {'quota' : 13024000000000000, 'used' : get_usage('atlas')}
  config['cms'] = {'quota' : 5440000000000000, 'used' : get_usage('cms')}
  config['dune'] = {'quota' : 1000000000000000, 'used' : get_usage('dune')}
  config['lhcb'] = {'quota' : 8370000000000000, 'used' : get_usage('lhcb')}

#  print config

  output = template.render(page=config)
  with open('storagesummary.json', 'w') as f:
    f.write(output)

  upload_summary('SRR.json','storagesummary.json')

#################################################################################
#
# get_version
#
#################################################################################

def get_version ():

  p = subprocess.Popen(["ceph", "version"], stdout=subprocess.PIPE)
  version = p.communicate()[0]
  return version.split()[2]

#################################################################################
#
# get_total_usage
#
#################################################################################

def get_total_usage ():

  p = subprocess.Popen(["ceph", "df", "-fjson"], stdout=subprocess.PIPE)
  df = json.loads(p.communicate()[0])
  usage = {}
  usage['totalused'] = df["stats"]["total_used_bytes"]
  usage['totalsize'] = df["stats"]["total_bytes"]
  return usage

#################################################################################
#
# get_usage
#
#################################################################################

def get_usage (VO):

  p = subprocess.Popen(["ceph", "df", "-fjson"], stdout=subprocess.PIPE)
  df = json.loads(p.communicate()[0])
  for pool in df["pools"]:
    if pool['name'] == VO:
      usage = pool['stats']['bytes_used']
  return usage

#################################################################################
#
# get_time - Returns the current time in seconds since the Epoc
#
#################################################################################

def get_time ():

  return int(time.time())

#################################################################################
#
# upload_summary - Uploads the json to the desired S3 bucket
#
#################################################################################

def upload_summary (s3_user, filename):
  with open(s3_user,'r') as cuif:
    user = json.load(cuif)

#  S3_ACCESS_KEY    =  user["keys"][0]["access_key"]
#  S3_SECRET_KEY    =  user["keys"][0]["secret_key"]

  conn = boto.connect_s3(
    aws_access_key_id = user["keys"][0]["access_key"],
    aws_secret_access_key = user["keys"][0]["secret_key"],
    host = 's3.echo.stfc.ac.uk',
    port = 443,
    is_secure=True,               # uncomment if you are not using ssl
    calling_format = boto.s3.connection.OrdinaryCallingFormat(),
    )
    
  k = Key(conn.get_bucket('srr'))
  k.key = 'storagesummary.json'
  k.set_contents_from_filename(filename)
  k.set_acl('public-read')
  today = str(date.today())
  k.key = 'storagesummary_' + today + '.json'
  k.set_contents_from_filename(filename)
  k.set_acl('public-read')

if __name__ == "__main__":
  main()
