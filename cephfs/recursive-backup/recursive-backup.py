#!/usr/bin/python3
import os
import sys
import json
import time
import shlex
import argparse
import subprocess
import configparser
from contextlib import redirect_stdout
from datetime import datetime, timedelta

warnings = False

def timestamp_print( message ):
    print ("# {} {}".format(time.strftime('[%Y-%m-%d %H:%M:%S]'), message))

def debug_print( message ):
    if (verbosity == "debug"):
        timestamp_print("DEBUG> " + message)

def info_print( message ):
    if (verbosity == "info" or verbosity == "debug"):
        timestamp_print("INFO> " + message)

def warn_print( message ):
    global warnings
    warnings = True
    timestamp_print("WARN> " + message)

def exit_print ( success, message ):
    if success:
        timestamp_print("FINISHED SUCCESS> " + message)
    else:
        timestamp_print("FINISHED FAILED> " + message)

def print_summary_json ( success, message ):
    body = {
        "type": "backup_summary",
        "success": success,
        "start_time": start_time,
        "exit_time": time.time(),
        "message": message
    }
    print(json.dumps(body))

def log_and_exit ( success, message ):
    if (args.run):
        print_summary_json( success, message)
    exit_print( success, message );
    rc = 1
    if success and not warnings:
        rc = 0
    sys.exit(rc)

start_time=time.time()

attrcmd = ["getfattr", "--only-values", "-n"]

verbosity="debug"
run_name="recursive-backup"
config = configparser.ConfigParser()

# populate defaults
config['DEFAULT']['backup_command'] = 'rsync -n -a --perms --acls --links --stats --no-hard-links --numeric-ids'
config['DEFAULT']['one_level_backup_command'] = 'rsync -n -a --perms --acls --links --stats --no-hard-links --numeric-ids -f -_/*/*'
config['DEFAULT']['max_files']="100000"
config['DEFAULT']['max_bytes']="1000000000000"
config['DEFAULT']['safety_factor']="3600"
config['DEFAULT']['verbosity']="none"
config['DEFAULT']['check_src']="true"
config['DEFAULT']['check_dst']="true"
config['DEFAULT']['check_pid']="true"
config['DEFAULT']['pid_dir']="/var/run/ceph-fs-backup"
config['DEFAULT']['check_space']="false"
config['DEFAULT']['free_bytes']="10000000000"
config['DEFAULT']['log_to_file']="false"
config['DEFAULT']['log_dir']="/var/log/ceph-fs-backup"

parser = argparse.ArgumentParser(description="Generate rsync commands to back up changes to a CephFS filesystem since a given time. Uses the CephFS rctime to determine what has changed, and uses rfiles and rbytes to determine the size of individual rsyncs. By default it will do nothing apart from outputting rsync commands to standard output.")

parser.add_argument("src", help="source CephFS directory to backup")
parser.add_argument("dst", help="destination directory to store the backup")
parser.add_argument("-n", "--name", help="name of the backup job (for log and pid file).", type=str)
parser.add_argument("-t", "--time", help="epoch time of last backup", type=int)
parser.add_argument("-d", "--days", help="days since last backup. Use instead of --time", type=int)
parser.add_argument("--full", help="do a full backup", action="store_true")
parser.add_argument("-f", "--maxfiles", help="maximum number of files per rsync. defaults to 100000", type=int)
parser.add_argument("-b", "--maxbytes", help="maximum bytes per rsync. defaults to 1TB", type=int)
parser.add_argument("-s", "--safety", help="number of seconds before last backup time to still consider the directory changed. defaults to 3600 (1h)", type=int)
parser.add_argument("--checksrc", help="(default) check if the source dir is mountpoint before starting", action="store_true")
parser.add_argument("--nochecksrc", help="do not check if the source dir is mountpoint before starting", action="store_true")
parser.add_argument("--checkdst", help="(default) check if the dest dir is mountpoint before starting", action="store_true")
parser.add_argument("--nocheckdst", help="do not check if the dest dir is mountpoint before starting", action="store_true")
parser.add_argument("--checkpid", help="(default) check for a named (-n/--name) pidfile before starting", action="store_true")
parser.add_argument("--nocheckpid", help="do not check for a named pidfile before starting", action="store_true")
parser.add_argument("--checkspace", help="when running the rsyncs, check for free space on destination FS before starting each rsync", action="store_true")
parser.add_argument("--nocheckspace", help="(default) do not check for free space on dest before starting each rsync", action="store_true")
parser.add_argument("--freebytes", help="specify amount of free space overhead needed on the destination to start an rsync. default is 100GB", type=int)
parser.add_argument("--run", help="run the rsyncs after generation", action="store_true")
parser.add_argument('-v', '--verbose', help="one '-v' for informational messages, two for debug", action='count', default=0)

args = parser.parse_args()

config.read('/etc/ceph-fs-backup/config.ini')

if args.name:
    run_name=args.name
    try:
        local_config = config[run_name]
    except:
        local_config = config['DEFAULT']
else:
    local_config = config['DEFAULT']

if args.run and not args.name: 
    log_and_exit( False, "name of backup job must be specified (--name/-n) when using the --run")

if not (args.time or args.days or args.full):
    log_and_exit( False, "backup interval not specified, use --time, --days or --full")

if (args.time and args.days) or (args.time and args.full) or (args.days and args.full):
    log_and_exit( False, "specify ONLY one of --time, --days or --full as a backup interval")

if args.safety:
    local_config['safety_factor'] = args.safety

if (args.verbose >= 2):
    local_config['verbosity'] = "debug"
elif (args.verbose == 1):
    local_config['verbosity'] = "info"

if (args.maxfiles != None):
    local_config['max_files'] = args.maxfiles

if (args.maxbytes != None):
    local_config['max_bytes'] = args.maxbytes

if args.checksrc and not args.nochecksrc:
    local_config['check_src'] = "True"
elif args.nochecksrc and not args.checksrc:
    local_config['check_src'] = "False"
elif args.nochecksrc and args.checksrc:
    log_and_exit( False, "--checksrc and --nochecksrc cannot both be used")

if args.checkdst and not args.nocheckdst:
    local_config['check_dst'] = "True"
elif args.nocheckdst and not args.checkdst:
    local_config['check_dst'] = "False"
elif args.nocheckdst and args.checkdst:
    log_and_exit( False, "--checkdst and --nocheckdst cannot both be used")

if args.checkpid and not args.nocheckpid:
    local_config['check_pid'] = "True"
elif args.nocheckpid and not args.checkpid:
    local_config['check_pid'] = "False"
elif args.nocheckpid and args.checkpid:
    log_and_exit( False, "--checkpid and --nocheckpid cannot both be used")

if args.checkspace and not args.nocheckspace:
    local_config['check_space'] = "True"
elif args.nocheckspace and not args.checkspace:
    local_config['check_space'] = "False"
elif args.nocheckspace and args.checkspace:
    log_and_exit( False, "--checkspace and --nocheckspace cannot both be used")



verbosity=local_config.get('verbosity')
backup_command = local_config.get('backup_command')
one_level_backup_command = local_config.get('one_level_backup_command')
max_files = local_config.getint('max_files')
max_bytes = local_config.getint('max_bytes')
safety_factor = local_config.getint('safety_factor')
check_src = local_config.getboolean('check_src')
check_dst = local_config.getboolean('check_dst')
check_pid = local_config.getboolean('check_pid')
check_space = local_config.getboolean('check_space')
free_bytes = local_config.getint('free_bytes')
log_dir = local_config.get('log_dir')
log_to_file = local_config.getboolean('log_to_file')
run = args.run
src = args.src
dst= args.dst

if log_to_file:
    log_file = os.path.join( log_dir, run_name + ".log" )
    info_print("stdout redirected to {}".format(log_file))
    sys.stdout = open(log_file, 'w')

# do not check for pidfile if not running the rsyncs
if not run:
    check_pid = False

if args.days:
    backup_time_obj = datetime.now() - timedelta(days=args.days)
    backup_time_wo_safety = backup_time_obj.timestamp()
    backup_time = backup_time_wo_safety - safety_factor
elif args.full:
    backup_time = 0
else:
    backup_time = args.time - safety_factor

info_print("backup time is {}".format(backup_time))

rsync_cmd_list = []
size_list = []

def rsync_full( directory, size ):
    generate_rsync( directory, size, False)

def rsync_one_level( directory ):
    generate_rsync( directory, 0, True)

def generate_rsync(directory, size, oneLevel):
    source = os.path.abspath(os.path.join(src,directory))
    destination =  os.path.abspath(os.path.join(dst,directory))
    src_dest_list = [source + "/", destination]
    if (oneLevel):
        cmd = one_level_backup_command.split() + src_dest_list
    else:
        cmd = backup_command.split() + src_dest_list
    rsync_cmd_list.append(cmd)
    size_list.append(size)
    if not run:
        print(" ".join(shlex.quote(s) for s in cmd))

def run_rsync( cmd ):
    rsync_sp = subprocess.run( cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
    return {"stdout": rsync_sp.stdout, "stderr": rsync_sp.stderr, "rc": rsync_sp.returncode}

def get_rctime( directory ):
    rctime_sp = subprocess.run(attrcmd + ["ceph.dir.rctime", directory], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if (rctime_sp.returncode == 0):
        rctime = rctime_sp.stdout.split(b'.')[0]
        # check for broken rctimes, identified by having a '0' nanosecond component
        # due to the bug that prefixes the nanosecond component with '09', we should check for
        # the string being '090' and '0'
        # https://tracker.ceph.com/issues/39943
        broken_rctime = False
        rctime_nano_string = rctime_sp.stdout.split(b'.')[1].decode()
        if (rctime_nano_string == '090' or rctime_nano_string == '0'):
            broken_rctime = True
        
        return {"out": int(rctime), "stderr": rctime_sp.stderr, "rc": rctime_sp.returncode, "broken" : broken_rctime }
    else:
        warn_print("error while getting rctime of: {}".format(directory))
        return {"out": 0, "stderr": rctime_sp.stderr, "rc": rctime_sp.returncode}

def get_rfiles( directory ):
    rfiles_sp = subprocess.run(attrcmd + ["ceph.dir.rfiles", directory], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if (rfiles_sp.returncode == 0):
        return {"out": int(rfiles_sp.stdout), "stderr": rfiles_sp.stderr, "rc": rfiles_sp.returncode}
    else:
        warn_print("error while getting rfiles of: {}".format(directory))
        return {"out": 0, "stderr": rfiles_sp.stderr, "rc": rfiles_sp.returncode}

def get_rbytes( directory ):
    rbytes_sp = subprocess.run(attrcmd + ["ceph.dir.rbytes", directory], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if (rbytes_sp.returncode == 0):
        return {"out": int(rbytes_sp.stdout), "stderr": rbytes_sp.stderr, "rc": rbytes_sp.returncode}
    else:
        warn_print("error while getting rbytes of: {}".format(directory))
        return {"out": 0, "stderr": rbytes_sp.stderr, "rc": rbytes_sp.returncode}

def get_rsubdirs( directory ):
    rsubdirs_sp = subprocess.run(attrcmd + ["ceph.dir.rsubdirs", directory], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if (rsubdirs_sp.returncode == 0):
        return {"out": int(rsubdirs_sp.stdout), "stderr": rsubdirs_sp.stderr, "rc": rsubdirs_sp.returncode}
    else:
        warn_print("error while getting rsubdirs of: {}".format(directory))
        return {"out": 0, "stderr": rsubdirs_sp.stderr, "rc": rsubdirs_sp.returncode}

def get_fs_freespace( directory ):
    statvfs = os.statvfs(directory)
    return statvfs.f_frsize * statvfs.f_bavail

def recurse_rsync( directory ):
    debug_print("starting recurse rsync for directory {}".format(directory))
    rctime = get_rctime( directory )
    if (rctime["rc"] == 0 and (rctime["out"] > backup_time or rctime["broken"] )):
        if (rctime["broken"]):
            info_print( "directory {} has an odd time of {} with no nanosecond component, backing up as rctime is not reliable".format(directory, rctime["out"]) )
        else:
            info_print( "directory {} has a newer rctime of {}, backing up".format(directory, rctime["out"]) )
            
        rsubdirs = get_rsubdirs( directory )
        rfiles = get_rfiles( directory )
        rbytes = get_rbytes( directory )
        if ((rfiles["rc"] == 0 and rfiles["out"] < max_files) and (rbytes["rc"] == 0 and rbytes["out"] < max_bytes)):
            info_print("directory {} has {} files and {} bytes, fewer than the max of {} files / {} bytes".format(directory, rfiles["out"], rbytes["out"], max_files, max_bytes))
            info_print("rsyncing full directory: {}".format(directory))
            rsync_full(directory, rbytes["out"])
        elif (rsubdirs["rc"] == 0 and rsubdirs["out"] <= 1): # no subdirs = 1 subdir...
            info_print("directory {} is bigger than allowed ({}/{} files, {}/{} bytes), but has no subdirs".format(directory, rfiles["out"], max_files, rbytes["out"], max_bytes))
            info_print("rsyncing full directory: {}".format(directory))
            rsync_full(directory, rbytes["out"])
        else:
            info_print("directory {} is bigger than allowed ({}/{} files, {}/{} bytes) and has subdirs. rsyncing top level and recursing into dirs".format(directory, rfiles["out"], max_files, rbytes["out"], max_bytes))
            rsync_one_level(directory)
            for path,subdirs,files in os.walk(directory):
                for subdir in subdirs:
                    if not os.path.islink( os.path.join(directory,subdir)):
                        recurse_rsync( os.path.join(directory,subdir))
                break
    elif (rctime["rc"] == 0):  
        debug_print( "directory {} has an older rctime of {}, skipping".format(directory, rctime["out"]) )
    else:
        warn_print( "nonzero exit code while getting rctime for {}, not backing up".format(directory) )



if (check_pid):
    pid_file_path = os.path.join( pid_dir, run_name + ".lock")
    debug_print("pid check start - looking for pidfile at {}".format(pid_file_path))
    if os.access(pid_file_path, os.F_OK):
        debug_print("pid file from previous run found")
        pid_file = open(pid_file_path, "r")
        pid_file.seek(0)
        old_pid = pid_file.read().splitlines()[0]
        debug_print("pid from previous run is {}".format(old_pid))
        if os.path.exists("/proc/%s" % old_pid):
            debug_print("pid ({}) from previous run is still running".format(old_pid))
            log_and_exit(success=False, message="Previous {} job was still running (pid {}). Backup cannot start".format(run_name, old_pid))
        else:
            debug_print( "previous pid file found for job {}, but program not running (pid {}), removing pid file".format(run_name, old_pid) )
            os.remove(pid_file_path)

    pid_file = open(pid_file_path, "w")
    pid = os.getpid()
    pid_file.write("%s" % pid)
    debug_print("writing pid {} to {}".format(pid, pid_file_path))
    pid_file.close()

if (check_src):
    srcmnt = os.path.ismount(src)
    if not srcmnt:
        log_and_exit(success=False, message="Source directory {} is not a mountpoint (and check specified)".format(src))

if (check_dst):
    dstmnt = os.path.ismount(dst)
    if not dstmnt:
        log_and_exit(success=False, message="Destination directory {} is not a mountpoint (and check specified)".format(dst))

debug_print( "changing to source directory {}".format(src) )
os.chdir( src )
test_rctime = get_rctime( "." )
if (test_rctime["rc"] != 0):
    log_and_exit(success=False, message="Source directory {} did not return a CephFS rctime, so probably is not a CephFS mount and cannot be backed up".format(src))
else:
    debug_print("src dir returned a cephFS rctime, starting ")

#time.sleep(10)
recurse_rsync( "." )

if (run):
    cmd_list_len = len(rsync_cmd_list)
    timestamp_print("{} rsync commands to run".format(cmd_list_len))
    for (i, rsync_cmd) in enumerate(rsync_cmd_list):
        timestamp_print("{}/{} running '{}'".format(i+1, cmd_list_len, " ".join(rsync_cmd)))
        if check_space:
            debug_print("space check requested for destination")
            cur_freespace = get_fs_freespace(dst)
            next_rsync_size = size_list[i]
            debug_print("next_rsync_size {}".format(next_rsync_size))
            free_space_after_rsync = cur_freespace - next_rsync_size
            debug_print("space check: {} free space on destination, at most {} bytes in next rsync".format(cur_freespace, next_rsync_size))
            if free_space_after_rsync < free_bytes:
                log_and_exit(success=False, message="backup aborted due to possibility of free space on destination dropping below free space threshold. {} out of {} required free bytes were avaliable ({} current free space, {} remote dir size)".format(free_space_after_rsync, free_bytes, cur_freespace, next_rsync_size))
            else:
                info_print("space check ok - at least {} free bytes will be avaliable after this rsync ({} required, {} current free space, {} remote dir size)".format(free_space_after_rsync, free_bytes, cur_freespace, next_rsync_size))
            
        rsync = run_rsync(rsync_cmd)
        if (rsync["rc"] == 0):
            timestamp_print("Success")
            print(rsync["stdout"].decode('ascii'))
        else:
            timestamp_print("failure (return code: {})".format(rsync["rc"]))
            print(rsync["stdout"].decode('ascii'))
            print(rsync["stderr"].decode('ascii'))
            warn_print("rsync failed, continuing")
    if warnings is True:
       log_and_exit(success=False, message="backup started at {} ({}) finished with warnings".format(time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(start_time)), start_time))
    else:
       log_and_exit(success=True, message="backup started at {} ({}) finished successfully".format( time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(start_time)), start_time))
