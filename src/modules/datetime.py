# DateTime
# Maintainer(s): SzaBee13
# Contributor(s): SzaBee13
# Reviewer(s): SzaBee13
from datetime import datetime
import time
import pytz
import socket
import struct
import dotenv
import os

TIME_SERVERS = ["pool.ntp.org", "time.google.com", "time.windows.com", "time.apple.com", "time.nist.gov", "time.cloudflare.com", "time.facebook.com", "time.twitter.com", "time.amazon.com"]
dotenv.load_dotenv()
PREFERED_TIME_SERVER = os.getenv("PREFERED_TIME_SERVER") or TIME_SERVERS[0] # the closest ntp pool is recommended for best performance, but you can change this to any of the available servers

def unix_timestamp() -> dict:
  """Returns the current UNIX timestamp.

  This attempts to query `PREFERED_TIME_SERVER` (and falls back through
  `TIME_SERVERS`) using a small NTP request implemented with the stdlib.
  If all servers fail, falls back to the local system time.
  """
  # Try NTP servers in order: preferred first, then the list
  servers = [PREFERED_TIME_SERVER] + [s for s in TIME_SERVERS if s != PREFERED_TIME_SERVER]

  for srv in servers:
    try:
      ts = _query_ntp_server(srv)
      return { "unix_timestamp": int(ts), "ntp_server": srv }
    except Exception:
      continue

  # Fallback to local time if NTP queries fail
  return { "unix_timestamp": int(time.time()), "ntp_server": "local" }


def _query_ntp_server(server: str, timeout: int = 2) -> int:
  """Query an NTP server and return the UNIX timestamp (int).

  Uses a minimal NTP client over UDP. No external dependencies required.
  Raises on failure.
  """
  port = 123
  addr = (server, port)
  # NTP request: first byte -> 0b00 011 011 = 0x1b (LI=0, VN=3, Mode=3)
  msg = b'\x1b' + 47 * b'\0'

  with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.settimeout(timeout)
    s.sendto(msg, addr)
    data, _ = s.recvfrom(1024)

  if len(data) < 48:
    raise ValueError("Invalid NTP response")

  # Transmit timestamp starts at byte 40 and is two 32-bit integers
  sec, frac = struct.unpack('!II', data[40:48])
  ntp_time = sec + float(frac) / 2**32
  # Convert NTP epoch (1900) to UNIX epoch (1970)
  unix_time = ntp_time - 2208988800
  return int(unix_time)

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