from geopy.exc import GeocoderUnavailable

from src.modules import datetime as mdatetime
from src.modules import geo as mgeo
from src.modules import text as mtext


def test_generate_password_uses_requested_length():
  password = mtext.generate_password(length=16, charset="ab")

  assert len(password["password"]) == 16
  assert set(password["password"]) <= {"a", "b"}


def test_count_returns_scalar_values():
  counts = mtext.count("One two. Three four.")

  assert counts == {
    "words": 4,
    "characters": 17,
    "sentences": 3,
    "paragraphs": 1,
  }


def test_datetime_format_uses_runtime_timestamp(monkeypatch):
  monkeypatch.setattr(mdatetime.time, "time", lambda: 1234567890)

  result = mdatetime.format_time()

  assert result["formatted_time"] == "2009-02-13 23:31:30"


def test_geo_returns_clean_service_error(monkeypatch):
  class BrokenGeo:
    def geocode(self, *_args, **_kwargs):
      raise GeocoderUnavailable("down")

  monkeypatch.setattr(mgeo, "_geolocator", lambda: BrokenGeo())

  result = mgeo.geocode("somewhere")

  assert result == {"error": "Geocoding service unavailable"}