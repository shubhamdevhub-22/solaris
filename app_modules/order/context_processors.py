


from django.conf import settings


def get_google_map_api_key(request):
    return ({"GOOGLE_MAP_API_KEY":settings.GOOGLE_MAP_API_KEY})
