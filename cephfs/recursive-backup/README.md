# CephFS Recursive Backup

## Description

This script generates rsync commands to back up changes to a CephFS filesystem since a given time. Uses the CephFS rctime to determine what has changed, and uses rfiles and rbytes to determine the size of individual rsyncs. By default it will do nothing apart from outputting rsync commands to standard output.

Using the --run option will allow the script to also run the generated rsyncs. In this mode it outputs a summary line when the script exits, which can be redirected to a log, and the nagios/icinga check can be used to report on the state of and time since the last backup. Any non zero exit code from any of the backup runs will cause the backup to be marked as failed.

The config file `/etc/cephfs-recursive-backup/config.ini` can be used to alter defaults, as well as set specific settings for named jobs (with the -n option). An example config file is present in this repo with all avaliable config file options specified, but it is not compulsory. Command line options will always override config file settings.

## Example usage

TODO

## Recursive backup script usage

```
usage: cephfs-recursive-backup.py [-h] [-n NAME] [-t TIME] [-d DAYS] [--full]
                           [-f MAXFILES] [-b MAXBYTES] [-s SAFETY]
                           [--checksrc] [--nochecksrc] [--checkdst]
                           [--nocheckdst] [--checkpid] [--nocheckpid]
                           [--checkspace] [--nocheckspace]
                           [--freebytes FREEBYTES] [--run] [-v]
                           src dst

Generate rsync commands to back up changes to a CephFS filesystem since a
given time. Uses the CephFS rctime to determine what has changed, and uses
rfiles and rbytes to determine the size of individual rsyncs. By default it
will do nothing apart from outputting rsync commands to standard output.

positional arguments:
  src                   source CephFS directory to backup
  dst                   destination directory to store the backup

optional arguments:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  name of the backup job (for log and pid file).
  -t TIME, --time TIME  epoch time of last backup
  -d DAYS, --days DAYS  days since last backup. Use instead of --time
  --full                do a full backup
  -f MAXFILES, --maxfiles MAXFILES
                        maximum number of files per rsync. defaults to 100000
  -b MAXBYTES, --maxbytes MAXBYTES
                        maximum bytes per rsync. defaults to 1TB
  -s SAFETY, --safety SAFETY
                        number of seconds before last backup time to still
                        consider the directory changed. defaults to 3600 (1h)
  --checksrc            (default) check if the source dir is mountpoint before
                        starting
  --nochecksrc          do not check if the source dir is mountpoint before
                        starting
  --checkdst            (default) check if the dest dir is mountpoint before
                        starting
  --nocheckdst          do not check if the dest dir is mountpoint before
                        starting
  --checkpid            (default) check for a named (-n/--name) pidfile before
                        starting
  --nocheckpid          do not check for a named pidfile before starting
  --checkspace          when running the rsyncs, check for free space on
                        destination FS before starting each rsync
  --nocheckspace        (default) do not check for free space on dest before
                        starting each rsync
  --freebytes FREEBYTES
                        specify amount of free space overhead needed on the
                        destination to start an rsync. default is 100GB
  --run                 run the rsyncs after generation
  -v, --verbose         one '-v' for informational messages, two for debug
```

## Nagios/Icinga check usage

```
usage: icinga_cephfs_backup_check.py [-h] -f LOGFILE -i INTERVAL

Check the status of a backup run by the CephFS recursive-backup script.

optional arguments:
  -h, --help            show this help message and exit
  -f LOGFILE, --logfile LOGFILE
                        log file from backup process
  -i INTERVAL, --interval INTERVAL
                        time allowed since last successful backup (in seconds)
```
