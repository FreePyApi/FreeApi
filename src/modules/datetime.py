# DateTime
# Maintainer(s): SzaBee13
# Contributor(s): SzaBee13
# Reviewer(s): SzaBee13
from datetime import datetime
import time
import pytz

def unix_timestamp() -> dict:
  """Returns the current UNIX timestamp."""
  return { "unix_timestamp": int(time.time()) }

def format_time(timestamp: int = int(time.time()), format: str = "%Y-%m-%d %H:%M:%S", timezone: str = "UTC") -> dict:
  """Formats a given UNIX timestamp into a human-readable string."""
  """EXAMPLE FORMATS
    %Y-%m-%d %H:%M:%S -> 2024-06-01 12:00:00
    %d/%m/%Y %I:%M %p -> 01/06/2024 12:00 PM
    %A, %B %d, %Y -> Saturday, June 01, 2024
  """

  tz = pytz.timezone(timezone)
  dt = datetime.fromtimestamp(timestamp, tz)
  return { "formatted_time": dt.strftime(format) }

def get_timezones() -> dict:
  """Returns a list of all available timezones."""
  return { "timezones": pytz.all_timezones }

def convert_timezone(timestamp: int = int(time.time()), from_tz: str = "UTC", to_tz: str = "UTC") -> dict:
  """Converts a given UNIX timestamp from one timezone to another."""
  tz_from = pytz.timezone(from_tz)
  tz_to = pytz.timezone(to_tz)
  dt_from = datetime.fromtimestamp(timestamp, tz_from)
  dt_to = dt_from.astimezone(tz_to)
  return { "converted_time": int(dt_to.timestamp()) }

def time_difference(timestamp1: int, timestamp2: int) -> dict:
  """Calculates the difference between two UNIX timestamps in seconds."""
  return { "time_difference_seconds": abs(timestamp1 - timestamp2) }

def is_leap_year(year: int) -> dict:
  """Determines if a given year is a leap year."""
  is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
  return { "is_leap_year": is_leap }

def day_of_week(timestamp: int = int(time.time()), timezone: str = "UTC") -> dict:
  """Returns the day of the week for a given UNIX timestamp."""
  tz = pytz.timezone(timezone)
  dt = datetime.fromtimestamp(timestamp, tz)
  return { "day_of_week": dt.strftime("%A") }

def summer_time(timestamp: int = int(time.time()), timezone: str = "UTC") -> dict:
  """Determines if a given UNIX timestamp falls within daylight saving time for a specified timezone."""
  tz = pytz.timezone(timezone)
  dt = datetime.fromtimestamp(timestamp, tz)
  is_dst = bool(dt.dst())
  return { "is_daylight_saving_time": is_dst }