#!/usr/bin/python
#########################################################################
# Deletes a list of files in the form:
# datadisk/rucio/mc15_14TeV/24/3d/HITS.09709777._000863.pool.root.1
# The file containing the input files is given as the argument
#
#########################################################################

import rados, sys, math

# Open connection to ATLAS pool
cluster = rados.Rados(conffile='/etc/ceph/ceph.conf')
cluster.connect()
ioctx = cluster.open_ioctx('atlas')


# Open file
with open(sys.argv[1]) as f:
    for line in f:
        filename = line.strip()
        chunk0 = filename + '.0000000000000000'

# Get filesize from first chunk
        try:
            filesize = int(ioctx.get_xattr(chunk0, "striper.size"))
            numberchunks = math.ceil(filesize / 67108864)
            print filename + " is made up of " + str(numberchunks) + " chunks"
        except:
            print chunk0 + " does not exist.  Skipping to next file."
            continue
# Delete all the chunks
        for i in range(0, int(numberchunks)):
            n = hex(i)[2:]
            chunk = filename + '.' + n.zfill(16)
            try:
                ioctx.remove_object(chunk)
            except:
                print chunk + " does not exist."
#                break

ioctx.close()
cluster.shutdown()
