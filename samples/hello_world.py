# -*- coding: utf-8 -*-
import pprint

from lnetatmo import NetatmoAPI, WeatherStation, get_auth_info_by_username_pass


def main():
    client_id = ""  # Your client ID from Netatmo app registration at http://dev.netatmo.com/dev/listapps
    client_secret = ""  # Your client app secret
    username = ""  # Your netatmo account username
    password = ""  # Your netatmo account password

    access_token, other_info = get_auth_info_by_username_pass(client_id,
                                                              client_secret,
                                                              username,
                                                              password)

    expires_in = other_info['expire_in']
    refresh_token = other_info['refresh_token']

    api = NetatmoAPI(
        client_id=client_id,
        client_secret=client_secret,
        access_token=access_token,
        refresh_token=refresh_token,
        expiration=expires_in,
        scope="read_station read_camera access_camera"
    )

    print(api.user)
    print(api.stations[0])
    pprint.pprint(api.measures)

    station = WeatherStation(**api.stations[0])

    pprint.pprint(api.stations[0])
    print(station.measures)


if __name__ == '__main__':
    main()
