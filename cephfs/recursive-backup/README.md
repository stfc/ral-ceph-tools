# CephFS Recursive Backup

## Description

This script generates rsync commands to back up changes to a CephFS filesystem since a given time. Uses the CephFS rctime to determine what has changed, and uses rfiles and rbytes to determine the size of individual rsyncs. By default it will do nothing apart from outputting rsync commands to standard output.

Using the --run option causes the script to also run the generated rsyncs. In this mode it outputs a summary line when the script exits, which can be redirected to a log, and the nagios/icinga check can be used to report on the state of and time since the last backup.

## Example usage

TODO

## Recursive backup script usage

```
usage: recursive-backup.py [-h] [-t TIME] [-d DAYS] [--full] [-f MAXFILES]
                           [-b MAXBYTES] [-s SAFETY] [--checksrc] [--checkdst]
                           [--run] [-v]
                           src dst

positional arguments:
  src                   source CephFS directory to backup
  dst                   destination directory to store the backup

optional arguments:
  -h, --help            show this help message and exit
  -t TIME, --time TIME  epoch time of last backup
  -d DAYS, --days DAYS  days since last backup. Use instead of --time
  --full                do a full backup
  -f MAXFILES, --maxfiles MAXFILES
                        maximum number of files per rsync. defaults to 100000
  -b MAXBYTES, --maxbytes MAXBYTES
                        maximum bytes per rsync. defaults to 100GB
  -s SAFETY, --safety SAFETY
                        number of seconds before last backup time to still
                        consider the directory changed. defaults to 3600 (1h)
  --checksrc            check if the source dir is mountpoint before starting
  --checkdst            check if the dest dir is mountpoint before starting
  --run                 run the rsyncs after generation
  -v, --verbose         one '-v' for informational messages, two for debug
```

## Nagios/Icinga check usage

```
usage: icinga_cephfs_backup_check.py [-h] log interval

Check the status of a backup run by the CephFS recursive-backup script.

positional arguments:
  log         log file from backup process
  interval    time allowed since last successful backup (in seconds)

optional arguments:
  -h, --help  show this help message and exit
```
