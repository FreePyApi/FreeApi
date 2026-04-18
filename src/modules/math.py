# Math
# Maintainer(s): SzaBee13
# Contributor(s): SzaBee13
# Reviewer(s): SzaBee13
import math
import json
from random import randint
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "assets" / "math" / "units.json"
try:
  with open(DATA_FILE, "r") as f:
    _DATA = json.load(f)
    CONVERSION_TABLE = _DATA.get("conversions", {})
    METRIC_SCHEME = _DATA.get("metric_scheme", {})
    UNIT_NAMES = _DATA.get("unit_names", {})
    DATA_UNITS_RAW = _DATA.get("data_units", {})
    DATA_UNITS = {}
    _DATA_UNITS_LOWER = {}
    # build flattened data-units map (base = bytes)
    def _init_data_units(raw):
      for k, v in raw.items():
        if isinstance(v, (int, float)):
          DATA_UNITS[k] = float(v)
          lk = k.lower()
          if lk not in DATA_UNITS and lk not in _DATA_UNITS_LOWER:
            _DATA_UNITS_LOWER[lk] = float(v)
        elif isinstance(v, dict):
          for sub_k, sub_v in v.items():
            mult = None
            if isinstance(sub_v, (int, float)):
              mult = float(sub_v)
            elif isinstance(sub_v, dict) and sub_v.get("type") == "binary" and "exp" in sub_v:
              try:
                mult = float(2 ** int(sub_v["exp"]))
              except Exception:
                mult = None
            if mult is not None:
              DATA_UNITS[sub_k] = mult
              lk = sub_k.lower()
              if lk not in DATA_UNITS and lk not in _DATA_UNITS_LOWER:
                _DATA_UNITS_LOWER[lk] = mult
    try:
      _init_data_units(DATA_UNITS_RAW)
    except Exception:
      DATA_UNITS = {}
      _DATA_UNITS_LOWER = {}
except Exception:
  CONVERSION_TABLE = {}
  METRIC_SCHEME = {}
  UNIT_NAMES = {}
  DATA_UNITS_RAW = {}
  DATA_UNITS = {}
  _DATA_UNITS_LOWER = {}

def _eval_formula(expr: str, x: float) -> float:
  return eval(expr, {"__builtins__": None, "math": math}, {"x": x})

def _get_data_unit_multiplier(unit: str):
  if not unit:
    return None
  # exact match first
  if unit in DATA_UNITS:
    return DATA_UNITS[unit]
  # fallback to lower-case map when unambiguous
  return _DATA_UNITS_LOWER.get(unit.lower())

def convert_units(value: float, conversion_type: str, return_format: str = "unit") -> dict:
  """Converts a value from one unit to another.

  Supported flows:
  - If `conversion_type` exists in `conversions` it will use that (scalar or formula).
  - If `conversion_type` is in the form "<from>_to_<to>" and both units exist in
    `metric_scheme`, the conversion will be computed using metric multipliers.
  The result includes optional human-readable unit names and the factor used.
  """
  if return_format not in ("unit", "name", "both"):
    return { "error": "Invalid return_format. Use 'unit', 'name', or 'both'." }
  # Direct lookup in conversions table (scalars or formula entries)
  entry = CONVERSION_TABLE.get(conversion_type)
  if entry is not None:
    # compute converted value
    if isinstance(entry, dict) and entry.get("type") == "formula":
      try:
        converted_value = _eval_formula(entry["expr"], value)
      except Exception as e:
        return { "error": f"Formula evaluation error: {e}" }
    else:
      try:
        converted_value = value * entry
      except Exception as e:
        return { "error": f"Conversion error: {e}" }

    result = { "converted_value": converted_value }
    # attempt to extract from/to units from the conversion_type (e.g. cm_to_in)
    if "_to_" in conversion_type:
      from_u, to_u = conversion_type.split("_to_", 1)
      if return_format in ("unit", "both"):
        result.update({ "from_unit": from_u, "to_unit": to_u })
      if return_format in ("name", "both"):
        result.update({ "from_unit_name": UNIT_NAMES.get(from_u, from_u), "to_unit_name": UNIT_NAMES.get(to_u, to_u) })
    return result

  # Try metric scheme conversion if pattern matches
  if "_to_" in conversion_type:
    try:
      from_u, to_u = conversion_type.split("_to_", 1)
    except ValueError:
      return { "error": "Unsupported conversion type format." }

    if from_u in METRIC_SCHEME and to_u in METRIC_SCHEME:
      try:
        # factor = metric[from] / metric[to]
        factor = METRIC_SCHEME[from_u] / METRIC_SCHEME[to_u]
        converted_value = value * factor
        result = { "converted_value": converted_value, "factor": factor }
        if return_format in ("unit", "both"):
          result.update({ "from_unit": from_u, "to_unit": to_u })
        if return_format in ("name", "both"):
          result.update({ "from_unit_name": UNIT_NAMES.get(from_u, from_u), "to_unit_name": UNIT_NAMES.get(to_u, to_u) })
        return result
      except Exception as e:
        return { "error": f"Metric conversion error: {e}" }

  # Try data-units conversion if units are data storage representations
  if "_to_" in conversion_type:
    try:
      from_u, to_u = conversion_type.split("_to_", 1)
    except ValueError:
      return { "error": "Unsupported conversion type format." }

    from_mult = _get_data_unit_multiplier(from_u)
    to_mult = _get_data_unit_multiplier(to_u)
    if from_mult is not None and to_mult is not None:
      try:
        factor = from_mult / to_mult
        converted_value = value * factor
        result = { "converted_value": converted_value, "factor": factor }
        if return_format in ("unit", "both"):
          result.update({ "from_unit": from_u, "to_unit": to_u })
        if return_format in ("name", "both"):
          result.update({ "from_unit_name": UNIT_NAMES.get(from_u, UNIT_NAMES.get(from_u.lower(), from_u)), "to_unit_name": UNIT_NAMES.get(to_u, UNIT_NAMES.get(to_u.lower(), to_u)) })
        return result
      except Exception as e:
        return { "error": f"Data unit conversion error: {e}" }

  return { "error": "Unsupported conversion type." }

def get_conversion_types() -> dict:
  """Returns available conversion information.

  - `conversion_types`: explicit conversions from the `conversions` table.
  - `metric_units`: units available in the `metric_scheme` for on-the-fly conversions.
  - `unit_names`: mapping of short unit codes to human-readable names.
  """
  return {
    "conversion_types": list(CONVERSION_TABLE.keys()),
    "metric_units": list(METRIC_SCHEME.keys()),
    "unit_names": UNIT_NAMES,
  }

def get_unit_names() -> dict:
  return UNIT_NAMES

def check_prime(number: int) -> dict:
  """Checks if a number is prime."""
  if number <= 1:
    return { "is_prime": False }
  for i in range(2, int(math.sqrt(number)) + 1):
    if number % i == 0:
      return { "is_prime": False }
  return { "is_prime": True }

def check_odd_even(number: int) -> dict:
  """Checks if a number is odd or even."""
  if number % 2 == 0:
    return { "is_even": True, "is_odd": False, "result": "even" }
  else:
    return { "is_even": False, "is_odd": True, "result": "odd" }

def factorial(n: int) -> dict:
  """Calculates the factorial of a number."""
  if n < 0:
    return { "error": "Factorial is not defined for negative numbers." }
  elif n == 0 or n == 1:
    return { "factorial": 1 }
  else:
    result = 1
    for i in range(2, n + 1):
      result *= i
    return { "factorial": result }

def random_number(min: int = 0, max: int = 100) -> dict:
  """Generates a random number between min and max."""
  if min > max:
    return { "error": "Minimum value cannot be greater than maximum value." }
  return { "random_number": randint(min, max) }

def fibonacci(n: int) -> dict:
  """Generates the Fibonacci sequence up to the nth number."""
  if n < 0:
    return { "error": "Fibonacci is not defined for negative numbers." }
  sequence = []
  a, b = 0, 1
  for _ in range(n):
    sequence.append(a)
    a, b = b, a + b
  return { "fibonacci_sequence": sequence }
