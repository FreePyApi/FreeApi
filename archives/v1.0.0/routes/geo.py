from typing import Any

from fastapi import APIRouter, Body

from ..modules import geo as mgeo

router = APIRouter()


@router.post("/geo/geocode", tags=["Geo"])
def geo_geocode(address: str = Body(..., min_length=1, max_length=500)) -> dict[str, Any]:
  return mgeo.geocode(address=address)


@router.post("/geo/is_sea", tags=["Geo"])
def geo_is_sea(latitude: float = Body(..., ge=-90, le=90), longitude: float = Body(..., ge=-180, le=180)) -> dict[str, Any]:
  return mgeo.is_sea(latitude=latitude, longitude=longitude)


@router.post("/geo/get_timezone", tags=["Geo"])
def geo_get_tz(latitude: float = Body(..., ge=-90, le=90), longitude: float = Body(..., ge=-180, le=180)) -> dict[str, Any]:
  return mgeo.get_timezone(latitude=latitude, longitude=longitude)


@router.post("/geo/get_address", tags=["Geo"])
def geo_get_addr(latitude: float = Body(..., ge=-90, le=90), longitude: float = Body(..., ge=-180, le=180)) -> dict[str, Any]:
  return mgeo.get_address(latitude=latitude, longitude=longitude)
