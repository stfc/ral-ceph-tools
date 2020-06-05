#!/usr/bin/python3
import os
import argparse
import subprocess

max_files=100000
max_bytes=1000000000000

attrcmd = ["getfattr", "--only-values", "-d", "-m"]

rsync_cmd = "rsync -a -v -n"
one_lvl_filter = " -f '- /*/*'"

parser = argparse.ArgumentParser()

parser.add_argument("src", help="source CephFS directory to backup")
parser.add_argument("dst", help="destination directory to store the backup")
parser.add_argument("time", help="epoch time of last backup (set to 0 for full sync)", type=int)
parser.add_argument("-f", "--maxfiles", help="maximum number of files per rsync", type=int)
parser.add_argument("-b", "--maxbytes", help="maximum bytes per rsync", type=int)
parser.add_argument("-d", "--debug", help="print debug statements", action="store_true")

args = parser.parse_args()

if (args.maxfiles != None):
	max_files = args.maxfiles

if (args.maxbytes != None):
	max_bytes = args.maxbytes

def debug_print( message ):
	if (args.debug):
		print("# DEBUG> " + message)

def rsync_full( directory ):
	generate_rsync( directory, False)

def rsync_one_level( directory ):
	generate_rsync( directory, True)

def generate_rsync(directory, oneLevel):
	source = os.path.abspath(os.path.join(args.src,directory))
	destination =  os.path.abspath(os.path.join(args.dst,directory))
	src_dest_str = " '{}/' '{}'".format(source, destination)
	if (oneLevel):
		cmd = rsync_cmd + one_lvl_filter + src_dest_str
	else:
		cmd = rsync_cmd + src_dest_str
	print(cmd)

def get_rctime( directory ):
	rctime_sp = subprocess.run(attrcmd + ["ceph.dir.rctime", directory], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	rctime = rctime_sp.stdout.split(b'.')[0]
	return {"out": int(rctime), "stderr": rctime_sp.stderr, "rc": int(rctime_sp.returncode)}

def get_rfiles( directory ):
        rfiles_sp = subprocess.run(attrcmd + ["ceph.dir.rfiles", directory], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return {"out": int(rfiles_sp.stdout), "stderr": rfiles_sp.stderr, "rc": int(rfiles_sp.returncode)}

def get_rbytes( directory ):
        rbytes_sp = subprocess.run(attrcmd + ["ceph.dir.rbytes", directory], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return {"out": int(rbytes_sp.stdout), "stderr": rbytes_sp.stderr, "rc": int(rbytes_sp.returncode)}


def get_rsubdirs( directory ):
        rsubdirs_sp = subprocess.run(attrcmd + ["ceph.dir.rsubdirs", directory], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return {"out": int(rsubdirs_sp.stdout), "stderr": rsubdirs_sp.stderr, "rc": int(rsubdirs_sp.returncode)}

def recurse_rsync( directory ):
	debug_print("starting recurse rsync for directory {}".format(directory))
	rctime = get_rctime( directory )
	if (rctime["rc"] == 0 and rctime["out"] > args.time):
		debug_print( "directory {} has a newer rctime of {}, backing up".format(directory, rctime["out"]) )
		rsubdirs = get_rsubdirs( directory )
		rfiles = get_rfiles( directory )
		rbytes = get_rbytes( directory )
		if ((rfiles["rc"] == 0 and rfiles["out"] < max_files) and (rbytes["rc"] == 0 and rbytes["out"] < max_bytes)):
			debug_print("directory {} has {} files and {} bytes, fewer than the max of {} files / {} bytes".format(directory, rfiles["out"], rbytes["out"], max_files, max_bytes))
			debug_print("rsyncing full directory: {}".format(directory))
			rsync_full(directory)
		elif (rsubdirs["rc"] == 0 and rsubdirs["out"] <= 1): # no subdirs = 1 subdir...
			debug_print("directory {} is bigger than allowed ({}/{} files, {}/{} bytes), but has no subdirs".format(directory, rfiles["out"], max_files, rbytes["out"], max_bytes))
			debug_print("rsyncing full directory: {}".format(directory))
			rsync_full(directory)
		else:
			debug_print("directory {} is bigger than allowed ({}/{} files, {}/{} bytes) and has subdirs. rsyncing top level and recursing into dirs".format(directory, rfiles["out"], max_files, rbytes["out"], max_bytes))
			rsync_one_level(directory)
                        for path,subdirs,files in os.walk(directory):
                                for subdir in subdirs:
                                        if not os.path.islink( os.path.join(directory,subdir)):
                                            recurse_rsync( os.path.join(directory,subdir))
                                break
	else:
	        debug_print( "directory {} has an older rctime of {}, skipping".format(directory, rctime["out"]) )


debug_print( "changing to directory {}".format(args.src) )
os.chdir( args.src )
recurse_rsync( "." )
