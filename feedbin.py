#!/usr/bin/env python
#
# get a list of starred urls from feedbin
#
import getpass
import urlparse
import oauth2 as oauth
import json
import os
import sys
import subprocess
import datetime
import time
import urllib
import httplib
import requests
import dateutil.parser

filename = os.path.join(os.path.dirname(__file__), ".feedbin")

base_url = "https://api.feedbin.me/v2/"

def call(verb, path, params=None):
    if verb == "GET":
        r = requests.get(base_url + path, auth=(username, password), params=params)
    elif verb == "POST":
        r = requests.get(base_url + path, auth=(username, password), params=params)
    elif verb == "DELETE":
        r = requests.delete(base_url + path, auth=(username, password), params=params)
    else:
        raise Exception("bad verb")
    if r.status_code == 200:
        return r.json()
    raise Exception(r.text)


try:
    with open(filename, "r") as f:
        username = f.readline().rstrip("\n\r")
        password = f.readline().rstrip("\n\r")
except IOError:
    username = raw_input("feedbin username:")
    password = getpass.getpass("feedbin password:")
    # test it first
    call("GET", "starred_entries.json")
    with open(filename, "w") as f:
        f.write("%s\n%s\n"%(username, password))



for entry_id in call("GET", "starred_entries.json"):
    try:
        entry = call("GET", "entries/%s.json"%entry_id)
    except Exception as e:
        print "Can't fetch entry %s: %s"%(entry_id, e)
        continue


    published = dateutil.parser.parse(entry["published"])
    url = entry["url"]
    filename = u"%s - %s - %s.mp4"%(entry["author"], published.strftime("%Y-%m-%d"), entry["title"])
    filename = filename.replace("/", "_").replace("%", "_")

    if not os.path.exists(filename):
        print u"downloading %s"%filename
        print "from %s"%url

        # https://en.wikipedia.org/wiki/YouTube#Quality_and_codecs
        format = "22"

        cmd = [sys.executable, "youtube-dl.py", "-f", format, "-o", filename, url]
        # print " ".join(cmd[1:])
        subprocess.call(cmd)
    else:
        print "File %s already exists"%filename

    if os.path.exists(filename):
        epoch = datetime.datetime.utcfromtimestamp(0)
        age = (published.replace(tzinfo=None) - epoch).total_seconds()
        os.utime(filename, (age, age))

        print "unstarring"
        call("DELETE", "starred_entries.json", {"starred_entries": [entry_id]})
