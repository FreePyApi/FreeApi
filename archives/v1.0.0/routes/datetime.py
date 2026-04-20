from time import time
from typing import Any, Optional

from fastapi import APIRouter, Query

from ..modules import datetime as mdatetime

router = APIRouter()


@router.get("/datetime/unix", tags=["DateTime"])
def get_unix_timestamp() -> dict[str, Any]:
  return mdatetime.unix_timestamp()


@router.get("/datetime/format", tags=["DateTime"])
def format_time(timestamp: Optional[int] = None, format: str = Query("%Y-%m-%d %H:%M:%S", max_length=100), timezone: str = Query("UTC", max_length=50)) -> dict[str, Any]:
  if timestamp is None:
    timestamp = int(time())
  return mdatetime.format_time(timestamp, format, timezone)


@router.get("/datetime/timezones", tags=["DateTime"])
def get_timezones() -> dict[str, Any]:
  return mdatetime.get_timezones()


@router.get("/datetime/convert/timezone", tags=["DateTime"])
def convert_timezone(timestamp: Optional[int] = None, from_tz: str = Query("UTC", max_length=50), to_tz: str = Query("UTC", max_length=50)) -> dict[str, Any]:
  if timestamp is None:
    timestamp = int(time())
  return mdatetime.convert_timezone(timestamp, from_tz, to_tz)


@router.get("/datetime/time_difference", tags=["DateTime"])
def time_difference(timestamp1: int = Query(...), timestamp2: int = Query(...)) -> dict[str, Any]:
  return mdatetime.time_difference(timestamp1, timestamp2)


@router.get("/datetime/is_leap_year", tags=["DateTime"])
def is_leap_year(year: int = Query(..., ge=1, le=9999)) -> dict[str, Any]:
  return mdatetime.is_leap_year(year)


@router.get("/datetime/day_of_week", tags=["DateTime"])
def day_of_week(timestamp: Optional[int] = None, timezone: str = Query("UTC", max_length=50)) -> dict[str, Any]:
  if timestamp is None:
    timestamp = int(time())
  return mdatetime.day_of_week(timestamp, timezone)


@router.get("/datetime/summer_time", tags=["DateTime"])
def summer_time(timestamp: Optional[int] = None, timezone: str = Query("UTC", max_length=50)) -> dict[str, Any]:
  if timestamp is None:
    timestamp = int(time())
  return mdatetime.summer_time(timestamp, timezone)
