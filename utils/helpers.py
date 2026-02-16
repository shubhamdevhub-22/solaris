from django.conf import settings
from geopy.geocoders import Nominatim
import requests


# def get_geo_code_from_address(address1, city, state, country):
#     """Return Geo code for provided address."""
#     try:
#         geolocator = Nominatim(user_agent="my_user_agent")
#         location = geolocator.geocode(f'{address1},{city},{state},{country}')
#     except Exception as e:
#         import traceback
#         print(traceback.format_exc())
#         return None
#     return location

def get_geo_code_from_address(address1, city, state, country):
    """Return Geo code for provided address."""
    location = None
    try:
        # geolocator = Nominatim(user_agent="my_user_agent")
        # location = geolocator.geocode(f'{address1},{city},{state},{country}')
        # print('➡ src/utils/helpers.py:10 location:', location)

        address = f'{address1},{city},{state},{country}'
        print('address: ', address)
        if address != None or address != "":
            api_key = settings.GOOGLE_MAP_API_KEY
            print('api_key: ', api_key)
            url = 'https://maps.googleapis.com/maps/api/geocode/json'
            params = {
                'address': address,
                'key': api_key
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'OK':
                    location = data['results'][0]['geometry']['location']
                    print('➡ src/utils/helpers.py:28 location:', location)
            else:
                print("error")
                location = None

    except Exception as e:
        print('e: ', e)
        import traceback
        print(traceback.format_exc())
        return None
    return location