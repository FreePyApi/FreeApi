from typing import Any

from fastapi import APIRouter, Body, Query, Path as ParamPath

from ..modules import uuid_hashing as muuid_hashing

router = APIRouter()


@router.get("/uuid/generate/{version}", tags=["UUID and Hashing"])
def uuid_generate(version: int = ParamPath(..., ge=1, le=5)) -> dict[str, Any]:
  return muuid_hashing.generate_uuid(version=version)


@router.get("/uuid/validate", tags=["UUID and Hashing"])
def uuid_validate(uuid_string: str = Query(..., min_length=1, max_length=100)) -> dict[str, Any]:
  return muuid_hashing.validate_uuid(uuid_string=uuid_string)


@router.get("/uuid/decode", tags=["UUID and Hashing"])
def uuid_decode(uuid_string: str = Query(..., min_length=1, max_length=200)) -> dict[str, Any]:
  return muuid_hashing.decode_uuid(uuid_string=uuid_string)


@router.post("/hash/string", tags=["UUID and Hashing"])
def hash_string(text: str = Body(..., min_length=1, max_length=5000), algorithm: str = Body("sha256", min_length=1, max_length=50)) -> dict[str, Any]:
  return muuid_hashing.hash_string(text=text, algorithm=algorithm)


@router.post("/hash/base64/encode", tags=["UUID and Hashing"])
def base64_encode(text: str = Body(..., min_length=1, max_length=10000)) -> dict[str, Any]:
  return muuid_hashing.base64_encode(text=text)


@router.post("/hash/base64/decode", tags=["UUID and Hashing"])
def base64_decode(encoded_text: str = Body(..., min_length=1, max_length=10000)) -> dict[str, Any]:
  return muuid_hashing.base64_decode(encoded_text=encoded_text)
