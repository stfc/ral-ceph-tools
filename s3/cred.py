#!/usr/bin/env python

from json import load

with open('current_user','r') as cuif:
    user = load(cuif)

USER_ID          =  user["user_id"]
DISPLAY_NAME     =  user["display_name"]
EMAIL            =  user["email"]
S3_ACCESS_KEY    =  user["keys"][0]["access_key"]
S3_SECRET_KEY    =  user["keys"][0]["secret_key"]
