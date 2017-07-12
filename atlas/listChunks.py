#!/usr/bin/env python

#########################################################################
# Produces a list of all the chunks in a pool of the form:
# datadisk/rucio/mc15_14TeV/24/3d/HITS.09709777._000863.pool.root.1.0000000000000000
#
#
#########################################################################

import rados, sys, gzip, time

pool_name = argv[1]
today = time.strftime('%Y%m%d') 
directory = "/root/filelistdumps/"

# Open connection to specified pool
cluster = rados.Rados(conffile='/etc/ceph/ceph.conf')
cluster.connect()
ioctx = cluster.open_ioctx(pool_name)

object_iterator = ioctx.list_objects()

outputfile = directory + pool_name + "/dump_" + today + ".gz"
with gzip.open(outputfile, 'wb') as f:

  while True :

    try :
      rados_object = object_iterator.next()
      f.write(rados_object.key)

    except StopIteration :
      break

f.close()
