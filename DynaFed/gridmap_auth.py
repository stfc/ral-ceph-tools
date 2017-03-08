#!/usr/bin/python
# -*- coding: utf-8 -*-

# Simple script that prints its arguments and then decides if the user has
# to be authorized
# usage:
# gridmap_auth.py <clientname> <remoteaddr> <fqan1> .. <fqanN>
#
# Return value means:
# 0 --> access is GRANTED
# nonzero --> access is DENIED
#

import sys, re

# A class that implements an authorization list loaded from a file during the initialization of the module.
# If this list is written only during initialization, and used as a read-only thing
# no synchronization primitives (e.g. semaphores) are needed, and the performance will be maximized
class _Authlist(object):
  GridMapFile = "/etc/grid-security/grid-mapfile"
  d = {}

  def __init__(self):
    print "Loading Gridmap file from " + self.GridMapFile
    with open(self.GridMapFile) as f:
      for line in f:
# Gridmap file looks like "/O=dutchgrid/O=users/O=nikhef/CN=Dominik Duda" atlasuser
# Split on '" ' in the middle and then strip of the leading " and trailing \n
        DN = (line.rsplit('" ')[0]).strip('"')
        Role = (line.split('" ')[-1]).strip('\n')
        self.d[DN] = Role

  def authenticateUser(self,DN):
    return DN in self.d

  def getRole(self, DN):
    return self.d[DN]

# Initialize a global instance of the authlist class, to be used inside the isallowed() function
myauthlist = _Authlist()

#regex = re.compile(r""\/CN=\w+$"")

def isallowed(clientname="unknown", remoteaddr="nowhere", resource="none", mode="0", fqans=None, keys=None):
#  print "clientname", clientname
#  print "remote address", remoteaddr
#  print "fqans", fqans
#  print "keys", keys
#  print "mode", mode
#  print "resource", resource

  # Deny access to anyone without a certificate in the GridMap File
#  altclientname = regex.sub("", clientname)
  altclientname = re.sub("\/CN=\w+$", "", clientname)
  print "Client name = " + clientname
  print "Client name with last entry removed = " + altclientname
# if not (myauthlist.authenticateUser(clientname) or myauthlist.authenticateUser(altclientname)):
#   return 1
  if not (myauthlist.authenticateUser(clientname)):
    if (myauthlist.authenticateUser(altclientname)):
      clientname = altclientname
    else:
      return 1


  # Read/list modes are always open
  if (mode == 'r') or (mode == 'l'):
    return 0

  # Allow atlasprod to do anything
  if (myauthlist.getRole(clientname) == 'atlasprod'):
    return 0

  # If any use case slips through deny access for safety
  return 1


#------------------------------
if __name__ == "__main__":
  r = isallowed(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])
  print r
  sys.exit(r)
