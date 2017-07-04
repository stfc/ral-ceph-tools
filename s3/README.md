## Introduction
This directory contains a list of scripts that can be used to perform basic operations on S3 buckets.

The scripts themselves do not contain any of the secret/access keys for the accounts. They assume there is a json file called current_user that contains the relevant information.
To get this information do:
```
radosgw-admin user info --uid <userID> > <userID>.json
ln -s <userID>.json current_user
```

## Scripts
#### list_buckets.py
Takes no arguments and will list the buckets for the userID.  Example:
```
./list_buckets.py
```

#### create_bucket.py
Takes one argument, the bucket name to be created.  Example:
```
./create_bucket.py <bucket name>
```

#### get_object.py
Fetches an object from a bucket and writes it to a file on your local disk.  Takes 3 arguments, the bucket name, the objectID and the filename you want to write to.  Example:
```
./get_object.py <bucket name> <objectID> <dst file>
```
