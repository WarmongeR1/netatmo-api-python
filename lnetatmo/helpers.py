# -*- coding: utf-8 -*-

import time
from sys import version_info

# HTTP libraries depends upon Python 2 or 3
if version_info.major == 3:
    pass
else:
    pass


# Global shortcut

def getStationMinMaxTH(station=None, module=None):
    authorization = ClientAuth()
    devList = DeviceList(authorization)
    if not station: station = devList.default_station
    if module:
        mname = module
    else:
        mname = devList.stationByName(station)['module_name']
    lastD = devList.lastData(station)
    if mname == "*":
        result = dict()
        for m in lastD.keys():
            if time.time() - lastD[m]['When'] > 3600: continue
            r = devList.MinMaxTH(module=m)
            result[m] = (r[0], lastD[m]['Temperature'], r[1])
    else:
        if time.time() - lastD[mname]['When'] > 3600:
            result = ["-", "-"]
        else:
            result = [lastD[mname]['Temperature'], lastD[mname]['Humidity']]
        result.extend(devList.MinMaxTH(station, mname))
    return result
