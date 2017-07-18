#!/usr/bin/env python

############################################################################
#
# Script that converts a list of castor nameserve paths into a list of transfer
# commands.
#
# If you are using FTS to transfer the files the CopyCommand should be left blank
#
############################################################################


fin = open("Collision10.list", "r")
fout = open("Transfers.sh", "w")

CopyCommand = ""
CastorSAPath = "srm://srm-lhcb.gridpp.rl.ac.uk/castor/ads.rl.ac.uk/"
EchoSAPath = "gsiftp://gridftp.echo.stfc.ac.uk/lhcb:"

#print EchoSAPath
for line in fin:
  lfn = line.strip().replace("/castor/ads.rl.ac.uk/", "")
  transfer = CopyCommand + CastorSAPath + lfn + " " + EchoSAPath + lfn + "\n"
  fout.write(transfer)
