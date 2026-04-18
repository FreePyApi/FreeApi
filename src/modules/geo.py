# Geo
# Maintainer(s): SzaBee13
# Contributor(s): SzaBee13
# Reviewer(s): SzaBee13
from geopy.geocoders import Nominatim

def geocode(address: str) -> dict:
  """Geocodes a given address into latitude and longitude."""
  geolocator = Nominatim(user_agent="freeapi")
  location = geolocator.geocode(address)
  if location:
    return { "latitude": location.latitude, "longitude": location.longitude }
  else:
    return { "error": "Address not found" }

def is_sea(latitude: float, longitude: float) -> dict:
  """Determines if a given latitude and longitude is located in the sea."""
  geolocator = Nominatim(user_agent="freeapi")
  location = geolocator.reverse((latitude, longitude), exactly_one=True)
  if location and 'sea' in location.raw.get('type', ''):
    return { "is_sea": True }
  else:
    return { "is_sea": False }

def get_timezone(latitude: float, longitude: float) -> dict:
  """Returns the timezone for a given latitude and longitude."""
  geolocator = Nominatim(user_agent="freeapi")
  location = geolocator.reverse((latitude, longitude), exactly_one=True)
  if location and 'timezone' in location.raw:
    return { "timezone": location.raw['timezone'] }
  else:
    return { "error": "Timezone not found" }

def get_address(latitude: float, longitude: float) -> dict:
  """Returns the address for a given latitude and longitude."""
  geolocator = Nominatim(user_agent="freeapi")
  location = geolocator.reverse((latitude, longitude), exactly_one=True)
  if location:
    return { "address": location.address }
  else:
    return { "error": "Address not found" }