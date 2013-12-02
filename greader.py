#!/usr/bin/env python
#
# get a list of starred urls from google reader.
# based on code from http://asktherelic.com/2010/04/26/accessing-google-reader-via-oauth-and-python/
#

# change these if you want to use in your own app
oauth_key = "movieos.org"
oauth_secret = "v9fA5GPFd+P5EZiBkQ+8l97S"
#


import urlparse
import oauth2 as oauth
import json
import os
import sys
import subprocess
import datetime
import time
import urllib

scope = "https://www.google.com/reader/api"
request_token_url = "https://www.google.com/accounts/OAuthGetRequestToken?scope=%s" % scope
authorize_url = 'https://www.google.com/accounts/OAuthAuthorizeToken'
access_token_url = 'https://www.google.com/accounts/OAuthGetAccessToken'
consumer = oauth.Consumer(oauth_key, oauth_secret)

try:
    # try to read access token from existing token file
    # TODO - give sensible name, put in ~
    with open(".token") as tokenfile:
        access_token = dict(urlparse.parse_qsl(tokenfile.read()))

except IOError:
    # token file doesn't exist.

    # get request token
    client = oauth.Client(consumer)
    resp, content = client.request(request_token_url, "GET")
    request_token = dict(urlparse.parse_qsl(content))

    # authorize
    print "Go to the following link in your browser:"
    print "%s?oauth_token=%s" % (authorize_url, request_token['oauth_token'])
    print
    print "Press enter once you're done."
    raw_input()

    # convert request token to access token
    token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
    client = oauth.Client(consumer, token)

    resp, content = client.request(access_token_url, "POST")

    with open(".token", "w") as tokenfile:
        tokenfile.write(content)

    print "Authenticated! Run script again to do things."
    sys.exit(1)


# We have an access token
token = oauth.Token(access_token['oauth_token'], access_token['oauth_token_secret'])
client = oauth.Client(consumer, token)

params = {
    "n": 1000,
    "ck": int(time.time()),
    "client": "movieos.org",
}
starred_url = '%s/0/stream/contents/user/-/state/com.google/starred?%s'%(scope, urllib.urlencode(params))
unstar_url = '%s/0/edit-tag'%(scope)
token_url = '%s/0/token'%scope

resp, post_token = client.request(token_url, 'GET')
if int(resp["status"]) != 200:
    print "can't get post token!"
    print post_token
    sys.exit(1)


resp, content = client.request(starred_url, 'GET')
starred = json.loads(content)
items = starred["items"]

print len(items), "items"

# reader returns 100 most recently starred things.
# earliest first still better than any other option.
items.sort(key=lambda i: i["published"])

for item in items:
    url = item["alternate"][0]["href"]
    if not "youtube.com" in url:
        continue

    # print json.dumps(item, indent=4)

    published = datetime.datetime(*(time.gmtime(int(item["published"])))[:6])
    filename = u"%s - %s - %s.mp4"%(item["author"], published.strftime("%Y-%m-%d"), item["title"])
    filename = filename.replace("/", "_")

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
        print "unstarring"
        os.utime(filename, (int(item["published"]), int(item["published"])))
        unstar = {
            "s": item["origin"]["streamId"],
            "i": item["id"],
            "r": "user/-/state/com.google/starred",
            "client": "movieos.org",
            "T": post_token,
        }
        client = oauth.Client(consumer, token)
        resp, content = client.request(unstar_url, 'POST', urllib.urlencode(unstar))
        if int(resp["status"]) != 200:
            print "Can't unstar!!"
            print resp
            print content
            sys.exit(1)



