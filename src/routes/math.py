from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query

from ..modules import math as mmath

router = APIRouter()


@router.post("/math/units/convert", tags=["Math", "Units"])
def convert_units(value: float = Body(...), conversion_type: str = Body(..., min_length=1, max_length=200), return_format: str = Body(..., min_length=1, max_length=50)) -> dict[str, Any]:
  return mmath.convert_units(value=value, conversion_type=conversion_type, return_format=return_format)


@router.get("/math/units/types", tags=["Math", "Units"])
def get_conversion_types() -> dict[str, Any]:
  return mmath.get_conversion_types()


@router.get("/math/units/names", tags=["Math", "Units"])
def get_unit_names() -> dict[str, Any]:
  return mmath.get_unit_names()


@router.post("/math/units/convert_numeric_system", tags=["Math", "Units"])
def convert_numeric_system(from_unit: str = Body("decimal", min_length=1, max_length=50), to_unit: str = Body("binary", min_length=1, max_length=50), value: str = Body(..., min_length=1, max_length=1000)) -> dict[str, Any]:
  return mmath.convert_numeric_system(from_unit=from_unit, to_unit=to_unit, value=value)


@router.get("/math/check/prime", tags=["Math"])
def check_prime(number: int = Query(..., ge=0)) -> dict[str, Any]:
  return mmath.check_prime(number=number)


@router.get("/math/check/odd_even", tags=["Math"])
def check_odd_even(number: int = Query(...)) -> dict[str, Any]:
  return mmath.check_odd_even(number=number)


@router.get("/math/factorial", tags=["Math"])
def factorial(n: int = Query(..., ge=0, le=1000)) -> dict[str, Any]:
  return mmath.factorial(n=n)


@router.get("/math/random_number", tags=["Math"])
def random_number(min: int = Query(0, ge=-2147483648), max: int = Query(100, ge=-2147483648)) -> dict[str, Any]:
  if max < min:
    raise HTTPException(status_code=400, detail="max must be >= min")
  return mmath.random_number(min=min, max=max)


@router.get("/math/fibonacci", tags=["Math"])
def fibonacci(n: int = Query(..., ge=0, le=10000)) -> dict[str, Any]:
  return mmath.fibonacci(n=n)
