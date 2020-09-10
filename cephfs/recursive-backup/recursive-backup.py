#!/usr/bin/python3
import os
import sys
import time
import shlex
import argparse
import subprocess

start_time=time.time()

max_files=100000
max_bytes=1000000000000
safety_factor=3600

attrcmd = ["getfattr", "--only-values", "-n"]

rsync_cmd = ["rsync", "-n", "-a", "--perms", "--acls", "--links", "--stats", "--delete", "--no-hard-links", "--numeric-ids"]
one_lvl_filter = ["-f", "-_/*/*"]

parser = argparse.ArgumentParser(description="Generate rsync commands to back up changes to a CephFS filesystem since a given time. Uses the CephFS rctime to determine what has changed, and uses rfiles and rbytes to determine the size of individual rsyncs. By default it will do nothing apart from outputting rsync commands to standard output.")

parser.add_argument("src", help="source CephFS directory to backup")
parser.add_argument("dst", help="destination directory to store the backup")
parser.add_argument("time", help="epoch time of last backup (set to 0 for full sync)", type=int)
parser.add_argument("-f", "--maxfiles", help="maximum number of files per rsync. defaults to 100000", type=int)
parser.add_argument("-b", "--maxbytes", help="maximum bytes per rsync. defaults to 100GB", type=int)
parser.add_argument("-s", "--safety", help="number of seconds before last backup time to still consider the directory changed. defaults to 3600 (1h)", type=int, default=3600)
parser.add_argument("--checksrc", help="check if the source dir is mountpoint before starting", action="store_true")
parser.add_argument("--checkdst", help="check if the dest dir is mountpoint before starting", action="store_true")
parser.add_argument("--run", help="run the rsyncs after generation", action="store_true")
parser.add_argument('-v', '--verbose', help="one '-v' for informational messages, two for debug", action='count', default=0)

args = parser.parse_args()

time = args.time - args.safety

debug = False
info = False
if (args.verbose >= 2):
    debug = True
elif (args.verbose == 1):
    info = True


if (args.maxfiles != None):
    max_files = args.maxfiles

if (args.maxbytes != None):
    max_bytes = args.maxbytes


rsync_cmd_list = []

def debug_print( message ):
    if (debug):
        print("# DEBUG> " + message)

def info_print( message ):
    if (info or debug):
        print("# INFO> " + message)


def rsync_full( directory ):
    generate_rsync( directory, False)

def rsync_one_level( directory ):
    generate_rsync( directory, True)

def generate_rsync(directory, oneLevel):
    source = os.path.abspath(os.path.join(args.src,directory))
    destination =  os.path.abspath(os.path.join(args.dst,directory))
    src_dest_list = [source + "/", destination]
    if (oneLevel):
        cmd = rsync_cmd + one_lvl_filter + src_dest_list
    else:
        cmd = rsync_cmd + src_dest_list
    rsync_cmd_list.append(cmd)
    if not args.run:
        print(" ".join(shlex.quote(s) for s in cmd))

def run_rsync( cmd ):
    rsync_sp = subprocess.run( cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
    return {"stdout": rsync_sp.stdout, "stderr": rsync_sp.stderr, "rc": rsync_sp.returncode}

def get_rctime( directory ):
    rctime_sp = subprocess.run(attrcmd + ["ceph.dir.rctime", directory], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if (rctime_sp.returncode == 0):
        rctime = rctime_sp.stdout.split(b'.')[0]
        return {"out": int(rctime), "stderr": rctime_sp.stderr, "rc": rctime_sp.returncode}
    else:
        return {"out": 0, "stderr": rctime_sp.stderr, "rc": rctime_sp.returncode}

def get_rfiles( directory ):
    rfiles_sp = subprocess.run(attrcmd + ["ceph.dir.rfiles", directory], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if (rfiles_sp.returncode == 0):
        return {"out": int(rfiles_sp.stdout), "stderr": rfiles_sp.stderr, "rc": rfiles_sp.returncode}
    else:
        return {"out": 0, "stderr": rfiles_sp.stderr, "rc": rfiles_sp.returncode}

def get_rbytes( directory ):
    rbytes_sp = subprocess.run(attrcmd + ["ceph.dir.rbytes", directory], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if (rbytes_sp.returncode == 0):
        return {"out": int(rbytes_sp.stdout), "stderr": rbytes_sp.stderr, "rc": rbytes_sp.returncode}
    else:
        return {"out": 0, "stderr": rbytes_sp.stderr, "rc": rbytes_sp.returncode}

def get_rsubdirs( directory ):
    rsubdirs_sp = subprocess.run(attrcmd + ["ceph.dir.rsubdirs", directory], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if (rsubdirs_sp.returncode == 0):
        return {"out": int(rsubdirs_sp.stdout), "stderr": rsubdirs_sp.stderr, "rc": rsubdirs_sp.returncode}
    else:
        return {"out": 0, "stderr": rsubdirs_sp.stderr, "rc": rsubdirs_sp.returncode}

def recurse_rsync( directory ):
    debug_print("starting recurse rsync for directory {}".format(directory))
    rctime = get_rctime( directory )
    if (rctime["rc"] == 0 and rctime["out"] > time):
        info_print( "directory {} has a newer rctime of {}, backing up".format(directory, rctime["out"]) )
        rsubdirs = get_rsubdirs( directory )
        rfiles = get_rfiles( directory )
        rbytes = get_rbytes( directory )
        if ((rfiles["rc"] == 0 and rfiles["out"] < max_files) and (rbytes["rc"] == 0 and rbytes["out"] < max_bytes)):
            info_print("directory {} has {} files and {} bytes, fewer than the max of {} files / {} bytes".format(directory, rfiles["out"], rbytes["out"], max_files, max_bytes))
            info_print("rsyncing full directory: {}".format(directory))
            rsync_full(directory)
        elif (rsubdirs["rc"] == 0 and rsubdirs["out"] <= 1): # no subdirs = 1 subdir...
            info_print("directory {} is bigger than allowed ({}/{} files, {}/{} bytes), but has no subdirs".format(directory, rfiles["out"], max_files, rbytes["out"], max_bytes))
            info_print("rsyncing full directory: {}".format(directory))
            rsync_full(directory)
        else:
            info_print("directory {} is bigger than allowed ({}/{} files, {}/{} bytes) and has subdirs. rsyncing top level and recursing into dirs".format(directory, rfiles["out"], max_files, rbytes["out"], max_bytes))
            rsync_one_level(directory)
            for path,subdirs,files in os.walk(directory):
                for subdir in subdirs:
                    if not os.path.islink( os.path.join(directory,subdir)):
                        recurse_rsync( os.path.join(directory,subdir))
                break
    else:
        debug_print( "directory {} has an older rctime of {}, skipping".format(directory, rctime["out"]) )


if (args.checksrc):
    srcmnt = os.path.ismount(args.src)
    if not srcmnt:
        print("source directory {} is not a mountpoint and check specified".format(args.src))
        print("backup exited with errors")
        sys.exit(1)

if (args.checkdst):
    dstmnt = os.path.ismount(args.dst)
    if not dstmnt:
        print("dest directory {} is not a mountpoint and check specified".format(args.dst))
        print("backup exited with errors")
        sys.exit(1)


debug_print( "changing to source directory {}".format(args.src) )
os.chdir( args.src )
test_rctime = get_rctime( "." )
if (test_rctime["rc"] != 0):
    print("source directory {} did not return a CephFS rctime, so probably is not a CephFS mount".format(args.src))
    print("backup exited with errors")
    sys.exit(1)
else:
    debug_print("src dir returned a cephFS rctime, starting ")

recurse_rsync( "." )

if (args.run):
    cmd_list_len = len(rsync_cmd_list)
    print("{} rsync commands to run".format(cmd_list_len))
    for (i, rsync_cmd) in enumerate(rsync_cmd_list):
        print("{}/{} running '{}'".format(i+1, cmd_list_len, " ".join(rsync_cmd)))
        rsync = run_rsync(rsync_cmd)
        if (rsync["rc"] == 0):
            print("Success")
            print(rsync["stdout"].decode('ascii'))
        else:
            print("failure (return code: {})".format(rsync["rc"]))
            print(rsync["stdout"].decode('ascii'))
            print(rsync["stderr"].decode('ascii'))
            print("backup exited with errors")
            sys.exit(1)
    print("SUCCESS: backup started at {} finished successfully".format(start_time))
