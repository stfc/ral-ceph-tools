#!/usr/bin/python
#########################################################################
# Downloads failing transfers and deletions with error code 201
# 
# Converts surls into a list of files that can be deleted by rados
# datadisk/rucio/mc15_14TeV/24/3d/HITS.09709777._000863.pool.root.1
#
#
#########################################################################

import urllib2, json
#import pprint

#pp = pprint.PrettyPrinter()
try:
    response = urllib2.urlopen("http://dashb-atlas-ddm.cern.ch/dashboard/request.py/details.json?tool=rucio&activity=Deletion&activity_default_exclude=Upload%2FDownload+(Job)&activity_default_exclude=Upload%2FDownload+(User)&activity_default_exclude=Analysis+Download&activity_default_exclude=Analysis+Upload&activity_default_exclude=Production+Download&activity_default_exclude=Production+Upload&activity_default_exclude=CLI+Download&activity_default_exclude=CLI+Upload&dst_site=RAL-LCG2-ECHO&state=DELETION_FAILED&error_code=201&offset=0&limit=500&interval=1440&prettyprint%27", timeout = 120)
    data = json.loads(response.read())
#    pp.pprint(data['details'])
except urllib2.URLError as e:
    print type(e)

# Iterate through the downloaded jsons and create a set of unique failed urls. 
uniqueUrls = set()
for entry in data['details']:
    uniqueUrls.add(entry['dst_url'])

#print uniqueUrls
# Write object IDs to a file
fout = open('/tmp/FilesToDelete.txt', 'w')
for url in uniqueUrls:
   newstr = url.replace("gsiftp://gridftp.echo.stfc.ac.uk:2811/atlas:", "")
   fout.write(newstr + "\n")

fout.close()
