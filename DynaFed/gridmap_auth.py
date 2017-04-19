#!/usr/bin/python
# -*- coding: utf-8 -*-

# Authorization plugin that uses an authDB and grid-mapfile
# usage:
# gridmap_auth.py <clientname> <remoteaddr> <fqan1> .. <fqanN>
#
# Return value means:
# 0 --> access is GRANTED
# nonzero --> access is DENIED
#

import sys, re, json

# A class that implements a grid-mapfile loaded from a text file during the initialization of the module.
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
#        print(self.d)

  def authenticateUser(self,DN):
    return DN in self.d

  def getRole(self, DN):
    return self.d[DN]


# A class that implements an authorization database loaded from a json file during the initialization of the module.
class _AuthDB(object):
  AuthDBFile = "/etc/grid-security/authdb.json"
  d = {}

  def __init__(self):
    print "Loading AuthDB file from " + self.AuthDBFile
    with open(self.AuthDBFile) as f:
      self.d = json.load(f)
#    print(self.d)

  def authorizedUsers(self,VO,bucket,mode):
#    print "VO name is " + VO
#    print "Bucket name is " + bucket
#    print "Mode is " + mode
    return self.d[VO][bucket][mode]

# Initialize a global instance of the authlist class, to be used inside the isallowed() function
myauthlist = _Authlist()
myauthDB = _AuthDB()

#regex = re.compile(r"CN=[[:alnum:][:blank:]]*$")

def isallowed(clientname="unknown", remoteaddr="nowhere", resource="none", mode="0", fqans=None, keys=None):
#  print "clientname", clientname
#  print "remote address", remoteaddr
#  print "fqans", fqans
#  print "keys", keys
#  print "mode", mode
#  print "resource", resource
  
  # Deny access to anyone without a certificate in the GridMap File
#  altclientname = regex.sub("", clientname)
#  altclientname = re.sub("CN=[[:alnum:][:blank:]]*$", "", clientname)
#  print clientname
#  print altclientname
#  if not (myauthlist.authenticateUser(clientname) or myauthlist.authenticateUser(altclientname)):
#    return 1

# Allow anyone to list the /gridpp directory
#  if ((mode == 'l' and resource == '/gridpp') or (mode == 'r' and resource == '/gridpp/')):
#    return 0
  
# bucket name can be extracted from resource which looks like: /gridpp/dteam-disk/test1 
# Split on '/' and take the 3rd entry
  path = resource.split('/')
  if(path[-1] == ''):
    del path[-1]
#  print(path)
  if (len(path) <= 1):
    return 1
  elif (len(path) == 2 or len(path) == 3):
#    if ((path[1] == 'gridpp') and (mode == 'r' or mode == 'l')):
    if (mode == 'r' or mode == 'l'):
      return 0
    else:
      return 1
#  elif (len(path) == 3):
#    VO = path[2]
#    bucket = 'default'
  else:
    VO = path[2]
    bucket = path[3]

  a = {}
  try:
    a = myauthDB.authorizedUsers(VO, bucket, mode)
#    print(a)
  except:
    return 1;

  for k, v in a.iteritems():
    if (k == "role" and myauthlist.getRole(clientname) in v):
#      print "Role matched " + myauthlist.getRole(clientname)
      return 0
    if (k == "clientname" and clientname in v): 
#      print "DN matched " + clientname
      return 0
    if (k == "remoteaddr" and remoteaddr in v):
#      print "Remote IP matched " + remoteaddr
      return 0

  # Read/list modes are always open
#  if (mode == 'r') or (mode == 'l'):
#    return 0
    
  # Allow atlasprod to do anything
#  if (myauthlist.getRole(clientname) == 'atlasprod'):
#    return 0
    
  # If any use case slips through deny access for safety
  return 1


#------------------------------
if __name__ == "__main__":
  r = isallowed(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])
  print r
  sys.exit(r)
