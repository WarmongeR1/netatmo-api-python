# -*- coding: utf-8 -*-

import json
import time
from sys import version_info

# HTTP libraries depends upon Python 2 or 3
if version_info.major == 3:
    import urllib.parse, urllib.request
else:
    from urllib import urlencode
    import urllib2


# Utilities routines

def post(url, params, json_resp=True, body_size=65535):
    # Netatmo response body size limited to 64k (should be under 16k)
    if version_info.major == 3:
        req = urllib.request.Request(url)
        req.add_header("Content-Type",
                       "application/x-www-form-urlencoded;charset=utf-8")
        params = urllib.parse.urlencode(params).encode('utf-8')
        resp = urllib.request.urlopen(req, params).read(body_size).decode(
            "utf-8")
    else:
        params = urlencode(params)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"}
        req = urllib2.Request(url=url, data=params, headers=headers)
        resp = urllib2.urlopen(req).read(body_size)
    if json_resp:
        return json.loads(resp)
    else:
        return resp


def toTimeString(value):
    return time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(int(value)))


def toEpoch(value):
    return int(time.mktime(time.strptime(value, "%Y-%m-%d_%H:%M:%S")))


def todayStamps():
    today = time.strftime("%Y-%m-%d")
    today = int(time.mktime(time.strptime(today, "%Y-%m-%d")))
    return today, today + 3600 * 24
