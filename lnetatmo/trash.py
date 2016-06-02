# -*- coding: utf-8 -*-

import time
import warnings
from sys import version_info

from .utils import *
from .api import *

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


# DEPRECATED
class WeatherStationData:
    """
    List the Weather Station devices (stations and modules)

    Args:
        authData (NetatmoAPI): Authentication information with a working access Token
    """

    def __init__(self, authData):
        self.getAuthToken = authData.access_token
        postParams = {
            "access_token": self.getAuthToken
        }
        resp = post(URL_STATION_DATA, postParams)
        self.rawData = resp['body']['devices']
        self.stations = {d['_id']: d for d in self.rawData}
        self.modules = dict()
        for i in range(len(self.rawData)):
            for m in self.rawData[i]['modules']:
                self.modules[m['_id']] = m
        self.default_station = list(self.stations.values())[0]['station_name']

    def modulesNamesList(self, station=None):
        res = [m['module_name'] for m in self.modules.values()]
        res.append(self.stationByName(station)['module_name'])
        return res

    def stationByName(self, station=None):
        if not station:
            station = self.default_station
        for i, s in self.stations.items():
            if s['station_name'] == station:
                return self.stations[i]
        return None

    def stationById(self, sid):
        return None if sid not in self.stations else self.stations[sid]

    def moduleByName(self, module, station=None):
        s = None
        if station:
            s = self.stationByName(station)
            if not s: return None
        for m in self.modules:
            mod = self.modules[m]
            if mod['module_name'] == module:
                if not s or mod['main_device'] == s['_id']: return mod
        return None

    def moduleById(self, mid, sid=None):
        s = self.stationById(sid) if sid else None
        if mid in self.modules:
            if s:
                for module in s['modules']:
                    if module['_id'] == mid:
                        return module
            else:
                return self.modules[mid]

    def lastData(self, station=None, exclude=0):
        s = self.stationByName(station)
        if not s: return None
        lastD = dict()
        # Define oldest acceptable sensor measure event
        limit = (time.time() - exclude) if exclude else 0
        ds = s['dashboard_data']
        if ds['time_utc'] > limit:
            lastD[s['module_name']] = ds.copy()
            lastD[s['module_name']]['When'] = lastD[s['module_name']].pop(
                "time_utc")
            lastD[s['module_name']]['wifi_status'] = s['wifi_status']
        for module in s["modules"]:
            ds = module['dashboard_data']
            if ds['time_utc'] > limit:
                lastD[module['module_name']] = ds.copy()
                lastD[module['module_name']]['When'] = lastD[
                    module['module_name']].pop("time_utc")
                # For potential use, add battery and radio coverage information to module data if present
                for i in ('battery_vp', 'rf_status'):
                    if i in module: lastD[module['module_name']][i] = module[i]
        return lastD

    def checkNotUpdated(self, station=None, delay=3600):
        res = self.lastData(station)
        ret = []
        for mn, v in res.items():
            if time.time() - v['When'] > delay: ret.append(mn)
        return ret if ret else None

    def checkUpdated(self, station=None, delay=3600):
        res = self.lastData(station)
        ret = []
        for mn, v in res.items():
            if time.time() - v['When'] < delay: ret.append(mn)
        return ret if ret else None

    def getMeasure(self, device_id, scale, mtype, module_id=None,
                   date_begin=None, date_end=None, limit=None, optimize=False,
                   real_time=False):
        postParams = {"access_token": self.getAuthToken}
        postParams['device_id'] = device_id
        if module_id: postParams['module_id'] = module_id
        postParams['scale'] = scale
        postParams['type'] = mtype
        if date_begin: postParams['date_begin'] = date_begin
        if date_end: postParams['date_end'] = date_end
        if limit: postParams['limit'] = limit
        postParams['optimize'] = "true" if optimize else "false"
        postParams['real_time'] = "true" if real_time else "false"
        return post(GET_MEASURE_REQ, postParams)

    def MinMaxTH(self, station=None, module=None, frame="last24"):
        if not station: station = self.default_station
        s = self.stationByName(station)
        if not s:
            s = self.stationById(station)
            if not s: return None
        if frame == "last24":
            end = time.time()
            start = end - 24 * 3600  # 24 hours ago
        elif frame == "day":
            start, end = todayStamps()
        if module and module != s['module_name']:
            m = self.moduleByName(module, s['station_name'])
            if not m:
                m = self.moduleById(s['_id'], module)
                if not m: return None
            # retrieve module's data
            resp = self.getMeasure(
                device_id=s['_id'],
                module_id=m['_id'],
                scale="max",
                mtype="Temperature,Humidity",
                date_begin=start,
                date_end=end)
        else:  # retrieve station's data
            resp = self.getMeasure(
                device_id=s['_id'],
                scale="max",
                mtype="Temperature,Humidity",
                date_begin=start,
                date_end=end)
        if resp:
            T = [v[0] for v in resp['body'].values()]
            H = [v[1] for v in resp['body'].values()]
            return min(T), max(T), min(H), max(H)
        else:
            return None


class DeviceList(WeatherStationData):
    """
    This class is now deprecated. Use WeatherStationData directly instead
    """
    warnings.warn("The 'DeviceList' class was renamed 'WeatherStationData'",
                  DeprecationWarning)
    pass


class WelcomeData:
    """
    List the Netatmo Welcome cameras informations (Homes, cameras, events, persons)

    Args:
        authData (NetatmoAPI): Authentication information with a working access Token
    """

    def __init__(self, authData):
        self.getAuthToken = authData.access_token
        postParams = {
            "access_token": self.getAuthToken
        }
        resp = post(GET_HOME_DATA_REQ, postParams)
        self.rawData = resp['body']
        self.homes = {d['id']: d for d in self.rawData['homes']}
        self.persons = dict()
        self.events = dict()
        self.cameras = dict()
        self.lastEvent = dict()
        for i in range(len(self.rawData['homes'])):
            nameHome = self.rawData['homes'][i]['name']
            if nameHome not in self.cameras:
                self.cameras[nameHome] = dict()
            for p in self.rawData['homes'][i]['persons']:
                self.persons[p['id']] = p
            for e in self.rawData['homes'][i]['events']:
                if e['camera_id'] not in self.events:
                    self.events[e['camera_id']] = dict()
                self.events[e['camera_id']][e['time']] = e
            for c in self.rawData['homes'][i]['cameras']:
                self.cameras[nameHome][c['id']] = c
        for camera in self.events:
            self.lastEvent[camera] = self.events[camera][
                sorted(self.events[camera])[-1]]
        self.default_home = list(self.homes.values())[0]['name']
        self.default_camera = list(self.cameras[self.default_home].values())[0]

    def homeById(self, hid):
        return None if hid not in self.homes else self.homes[hid]

    def homeByName(self, home=None):
        if not home: home = self.default_home
        for key, value in self.homes.items():
            if value['name'] == home:
                return self.homes[key]

    def cameraById(self, cid):
        for home, cam in self.cameras.items():
            if cid in self.cameras[home]:
                return self.cameras[home][cid]
        return None

    def cameraByName(self, camera=None, home=None):
        if not camera and not home:
            return self.default_camera
        elif home and camera:
            if home not in self.cameras:
                return None
            for cam_id in self.cameras[home]:
                if self.cameras[home][cam_id]['name'] == camera:
                    return self.cameras[home][cam_id]
        elif not home and camera:
            for home, cam_ids in self.cameras.items():
                for cam_id in cam_ids:
                    if self.cameras[home][cam_id]['name'] == camera:
                        return self.cameras[home][cam_id]
        else:
            return list(self.cameras[home].values())[0]
        return None

    def cameraUrls(self, camera=None, home=None, cid=None):
        """
        Return the vpn_url and the local_url (if available) of a given camera
        in order to access to its live feed
        """
        local_url = None
        vpn_url = None
        if cid:
            camera_data = self.cameraById(cid)
        else:
            camera_data = self.cameraByName(camera=camera, home=home)
        if camera_data:
            vpn_url = camera_data['vpn_url']
            if camera_data['is_local']:
                resp = post(
                    '{0}/command/ping'.format(camera_data['vpn_url']), dict())
                temp_local_url = resp['local_url']
                resp = post('{0}/command/ping'.format(temp_local_url),
                            dict())
                if temp_local_url == resp['local_url']:
                    local_url = temp_local_url
        return vpn_url, local_url

    def personsAtHome(self, home=None):
        """
        Return the list of known persons who are currently at home
        """
        if not home: home = self.default_home
        home_data = self.homeByName(home)
        atHome = []
        for p in home_data['persons']:
            # Only check known persons
            if 'pseudo' in p:
                if not p["out_of_sight"]:
                    atHome.append(p['pseudo'])
        return atHome

    def getCameraPicture(self, image_id, key):
        """
        Download a specific image (of an event or user face) from the camera
        """
        postParams = {
            "access_token": self.getAuthToken,
            "image_id": image_id,
            "key": key
        }
        resp = post(GET_CAMERA_PICTURE_REQ, postParams, json_resp=False,
                    body_size=None)
        image_type = imghdr.what('NONE.FILE', resp)
        return resp, image_type

    def getProfileImage(self, name):
        """
        Retrieve the face of a given person
        """
        for p in self.persons:
            if 'pseudo' in self.persons[p]:
                if name == self.persons[p]['pseudo']:
                    image_id = self.persons[p]['face']['id']
                    key = self.persons[p]['face']['key']
                    return self.getCameraPicture(image_id, key)
        return None, None

    def updateEvent(self, event=None, home=None):
        """
        Update the list of event with the latest ones
        """
        if not home: home = self.default_home
        if not event:
            # If not event is provided we need to retrieve the oldest of the last event seen by each camera
            listEvent = dict()
            for cam_id in self.lastEvent:
                listEvent[self.lastEvent[cam_id]['time']] = self.lastEvent[
                    cam_id]
            event = listEvent[sorted(listEvent)[0]]

        home_data = self.homeByName(home)
        postParams = {
            "access_token": self.getAuthToken,
            "home_id": home_data['id'],
            "event_id": event['id']
        }
        resp = post(GET_EVENT_SUN_TIL_REQ, postParams)
        eventList = resp['body']['events_list']
        for e in eventList:
            self.events[e['camera_id']][e['time']] = e
        for camera in self.events:
            self.lastEvent[camera] = self.events[camera][
                sorted(self.events[camera])[-1]]

    def personSeenByCamera(self, name, home=None, camera=None):
        """
        Return True if a specific person has been seen by a camera
        """
        try:
            cam_id = self.cameraByName(camera=camera, home=home)['id']
        except TypeError:
            print("personSeenByCamera: Camera name or home is unknown")
            return False
        # Check in the last event is someone known has been seen
        if self.lastEvent[cam_id]['type'] == 'person':
            person_id = self.lastEvent[cam_id]['person_id']
            if 'pseudo' in self.persons[person_id]:
                if self.persons[person_id]['pseudo'] == name:
                    return True
        return False

    def _knownPersons(self):
        known_persons = dict()
        for p_id, p in self.persons.items():
            if 'pseudo' in p:
                known_persons[p_id] = p
        return known_persons

    def someoneKnownSeen(self, home=None, camera=None):
        """
        Return True if someone known has been seen
        """
        try:
            cam_id = self.cameraByName(camera=camera, home=home)['id']
        except TypeError:
            print("personSeenByCamera: Camera name or home is unknown")
            return False
        # Check in the last event is someone known has been seen
        if self.lastEvent[cam_id]['type'] == 'person':
            if self.lastEvent[cam_id]['person_id'] in self._knownPersons():
                return True
        return False

    def someoneUnknownSeen(self, home=None, camera=None):
        """
        Return True if someone unknown has been seen
        """
        try:
            cam_id = self.cameraByName(camera=camera, home=home)['id']
        except TypeError:
            print("personSeenByCamera: Camera name or home is unknown")
            return False
        # Check in the last event is someone known has been seen
        if self.lastEvent[cam_id]['type'] == 'person':
            if self.lastEvent[cam_id]['person_id'] not in self._knownPersons():
                return True
        return False

    def motionDetected(self, home=None, camera=None):
        """
        Return True if movement has been detected
        """
        try:
            cam_id = self.cameraByName(camera=camera, home=home)['id']
        except TypeError:
            print("personSeenByCamera: Camera name or home is unknown")
            return False
        if self.lastEvent[cam_id]['type'] == 'movement':
            return True
        return False
