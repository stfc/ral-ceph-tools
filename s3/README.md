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
Takes no arguments and will list the buckets for the userID.

#### create_bucket.py
Takes one argument
Example:
```


