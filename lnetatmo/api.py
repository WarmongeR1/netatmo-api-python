# -*- coding: utf-8 -*-


"""
This API provides access to the Netatmo weather station or/and the
    Welcome camera
This package can be used with Python2 or Python3 applications and do not
require anything else than standard libraries

PythonAPI Netatmo REST data access
"""

from .utils import *

BASE_URL = "https://api.netatmo.net/"
AUTH_REQ = BASE_URL + "oauth2/token"
GET_MEASURE_REQ = BASE_URL + "api/getmeasure"
URL_STATION_DATA = BASE_URL + "api/getstationsdata"
GET_HOME_DATA_REQ = BASE_URL + "api/gethomedata"
GET_CAMERA_PICTURE_REQ = BASE_URL + "api/getcamerapicture"
GET_EVENT_SUN_TIL_REQ = BASE_URL + "api/geteventsuntil"


def get_auth_info_by_username_pass(client_id,
                                   client_secret,
                                   username,
                                   password,
                                   scope='read_station'):
    payload = {
        "grant_type": "password",
        "client_id": client_id,
        "client_secret": client_secret,
        "username": username,
        "password": password,
        "scope": scope
    }
    response = post(AUTH_REQ, payload)
    response['expire_in'] = _prepare_expire_in(response['expire_in'])
    return response['access_token'], response


def _prepare_expire_in(value):
    return int(value + time.time())


class NetatmoAPI:
    """
    Request authentication and keep access token available through token method.
        Renew it automatically if necessary

    Args:
        client_id (str): Application clientId delivered by Netatmo
            on dev.netatmo.com
        client_secret (str): Application Secret key delivered by Netatmo
            on dev.netatmo.com
        access_token (str)
        refresh_token (optional(str))
        expiration (optional(int))
        scope (Optional[str]): Default value is 'read_station'
            read_station: to retrieve weather station data (Getstationsdata,
                Getmeasure)
            read_camera: to retrieve Welcome data (Gethomedata,
                Getcamerapicture)
            access_camera: to access the camera, the videos and the live stream.
            Several value can be used at the same time, ie:
                'read_station read_camera'
    """

    def __init__(self, client_id,
                 client_secret,
                 access_token,
                 refresh_token=None,
                 expiration=None,
                 scope="read_station"):

        self.expiration = None
        self.refresh_token = None

        self.client_id = client_id
        self.client_secret = client_secret
        self._scope = scope
        self._access_token = access_token
        if refresh_token is not None:
            self.refresh_token = refresh_token
        if expiration is not None:
            self.expiration = expiration
        self._stations = None

    def set_refresh_token(self, refresh_token):
        self.refresh_token = refresh_token

    def refresh_token(self):
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        response = post(AUTH_REQ, payload)
        self._access_token = response['access_token']
        self.refresh_token = response['refresh_token']
        self.expiration = int(response['expire_in'] + time.time())
        return response

    @property
    def access_token(self):
        if self.expiration is not None and self.expiration < time.time():
            if self.refresh_token is None:
                raise ValueError(
                    "Not found refresh_token, use set_refresh_token to set it")
            self.refresh_token()
        return self._access_token

    @property
    def user(self):
        response = post(URL_STATION_DATA, {"access_token": self.access_token})
        return response['body']['user']

    @property
    def email(self):
        response = post(URL_STATION_DATA, {"access_token": self.access_token})
        return response['body']['user']['mail']

    @property
    def stations(self):
        if self._stations is None:
            response = post(URL_STATION_DATA,
                            {"access_token": self.access_token})
            self._stations = response['body']['devices']
        return [WeatherStation(**x) for x in self._stations]

    @property
    def measures(self):
        return [x.measures for x in self.stations]


class WeatherStation:
    def __init__(self, **kwargs):
        self.station = kwargs
        self._modules = None

    @property
    def modules(self):
        if self._modules is None:
            self._modules = {x['_id']: x for x in self.station['modules']}
        return self._modules

    @property
    def modules_names(self):
        return [x['module_name'] for x in self.modules.values()]

    @property
    def name(self):
        return self.station['station_name']

    @property
    def measures(self):
        data = self.station.get('dashboard_data')
        data.update({
            'name': self.name
        })
        return data
