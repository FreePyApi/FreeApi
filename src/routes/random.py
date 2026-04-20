from typing import Any, Optional

from fastapi import APIRouter, Query

from ..modules import random as mrandom
from ..services.random import parse_explicit_filters

router = APIRouter()


@router.get("/random/color", tags=["Random"])
def random_color() -> dict[str, Any]:
  return mrandom.random_color()


@router.get("/random/gradient", tags=["Random"])
def random_gradient(colors: int = Query(2, ge=2), type: str = Query("linear", ge=2)) -> dict[str, Any]:
  return mrandom.random_gradient(colors=colors, type=type)


@router.get("/random/quote", tags=["Random"])
def random_quote(tag: str = Query(None)) -> dict[str, Any]:
  return mrandom.random_quote(tag=tag)


@router.get("/random/joke", tags=["Random"])
def random_joke(category: str = Query(None), explicit: Optional[str] = Query(None)) -> dict[str, Any]:
  explicit_filters = parse_explicit_filters(explicit)
  if "error" in explicit_filters:
    return explicit_filters

  return mrandom.random_joke(category=category, explicit=explicit_filters)


@router.get("/random/dad_joke", tags=["Random"])
def random_dad_joke(category: str = Query(None)) -> dict[str, Any]:
  return mrandom.random_dad_joke(category=category)
