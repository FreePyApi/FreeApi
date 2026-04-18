# Geo
# Maintainer(s): SzaBee13
# Contributor(s): SzaBee13
# Reviewer(s): SzaBee13
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable


def _geolocator() -> Nominatim:
  return Nominatim(user_agent="freeapi", timeout=10)


def _service_unavailable() -> dict:
  return {"error": "Geocoding service unavailable"}

def geocode(address: str) -> dict:
  """Geocodes a given address into latitude and longitude."""
  try:
    location = _geolocator().geocode(address)
  except (GeocoderTimedOut, GeocoderUnavailable):
    return _service_unavailable()

  if location:
    return { "latitude": location.latitude, "longitude": location.longitude }
  return { "error": "Address not found" }

def is_sea(latitude: float, longitude: float) -> dict:
  """Determines if a given latitude and longitude is located in the sea."""
  try:
    location = _geolocator().reverse((latitude, longitude), exactly_one=True)
  except (GeocoderTimedOut, GeocoderUnavailable):
    return _service_unavailable()

  if location and 'sea' in location.raw.get('type', ''):
    return { "is_sea": True }
  return { "is_sea": False }

def get_timezone(latitude: float, longitude: float) -> dict:
  """Returns the timezone for a given latitude and longitude."""
  try:
    location = _geolocator().reverse((latitude, longitude), exactly_one=True)
  except (GeocoderTimedOut, GeocoderUnavailable):
    return _service_unavailable()

  if location and 'timezone' in location.raw:
    return { "timezone": location.raw['timezone'] }
  return { "error": "Timezone not found" }

def get_address(latitude: float, longitude: float) -> dict:
  """Returns the address for a given latitude and longitude."""
  try:
    location = _geolocator().reverse((latitude, longitude), exactly_one=True)
  except (GeocoderTimedOut, GeocoderUnavailable):
    return _service_unavailable()

  if location:
    return { "address": location.address }
  return { "error": "Address not found" }