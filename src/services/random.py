import json
from typing import Any, Optional


def parse_explicit_filters(explicit: Optional[str]) -> dict[str, Any]:
  default_explicit = {
    "nsfw": False,
    "religious": False,
    "political": False,
    "racist": False,
    "sexist": False,
    "explicit": False,
  }
  if explicit is None:
    return default_explicit

  try:
    explicit_dict = json.loads(explicit)
    if not isinstance(explicit_dict, dict):
      return {"error": "Invalid explicit parameter; must be a JSON object.", "code": 400}
  except Exception:
    return {"error": "Invalid explicit parameter; must be valid JSON.", "code": 400}

  return explicit_dict
