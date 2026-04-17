# Math
# Maintainer(s): SzaBee13
# Contributor(s): SzaBee13
import math
from random import randint

CONVERSION_TABLE = {
  # Distance
  "cm_to_inch": 0.393701,
  "inch_to_cm": 2.54,
  "m_to_ft": 3.28084,
  "ft_to_m": 0.3048,
  "km_to_mile": 0.621371,
  "mile_to_km": 1.60934,
  "cm_to_ft": 0.0328084,
  "ft_to_cm": 30.48,
  # Weight/Mass
  "kg_to_lb": 2.20462,
  "lb_to_kg": 0.453592,
  "g_to_oz": 0.035274,
  "oz_to_g": 28.3495,
  "ton_to_kg": 1000,
  "kg_to_ton": 0.001,
  # Temperature
  "c_to_f": lambda c: (c * 9/5) + 32,
  "f_to_c": lambda f: (f - 32) * 5/9,
  "c_to_k": lambda c: c + 273.15,
  "k_to_c": lambda k: k - 273.15,
  "f_to_k": lambda f: (f - 32) * 5/9 + 273.15,
  "k_to_f": lambda k: (k - 273.15) * 9/5 + 32,
  # Volume
  "liter_to_gallon": 0.264172,
  "gallon_to_liter": 3.78541,
  "ml_to_floz": 0.033814,
  "floz_to_ml": 29.5735,
  "liter_to_cup": 4.22675,
  "cup_to_liter": 0.236588,
  "liter_to_pint": 2.11338,
  "pint_to_liter": 0.473176,
  "liter_to_quart": 1.05669,
  "quart_to_liter": 0.946353,
  "liter_to_cbm": 0.001,
  "cbm_to_liter": 1000,
  # Area
  "sqm_to_sqft": 10.7639,
  "sqft_to_sqm": 0.092903,
  "acre_to_sqm": 4046.86,
  "sqm_to_acre": 0.000247105,
  "hectare_to_sqm": 10000,
  "sqm_to_hectare": 0.0001,
  # Data Storage
  "byte_to_kb": 0.001,
  "kb_to_byte": 1000,
  "kb_to_mb": 0.001,
  "mb_to_kb": 1000,
  "mb_to_gb": 0.001,
  "gb_to_mb": 1000,
  "gb_to_tb": 0.001,
  "tb_to_gb": 1000,
  "bit_to_byte": 0.125,
  "byte_to_bit": 8,
  "gib_to_gb": 1.07374,
  "gb_to_gib": 0.931323,
  "mib_to_mb": 1.04858,
  "mb_to_mib": 0.953674,
  "kib_to_kb": 1.024,
  "kb_to_kib": 0.976562,
  "tib_to_tb": 1.09951,
  "tb_to_tib": 0.909495
}

def convert_units(value: float, conversion_type: str) -> dict:
  """Converts a value from one unit to another based on the conversion type."""
  if conversion_type in CONVERSION_TABLE:
    conversion = CONVERSION_TABLE[conversion_type]
    if callable(conversion):
      converted_value = conversion(value)
    else:
      converted_value = value * conversion
    return { "converted_value": converted_value }
  else:
    return { "error": "Unsupported conversion type." }

def get_conversion_types() -> dict:
  """Returns a list of supported conversion types."""
  return { "conversion_types": list(CONVERSION_TABLE.keys()) }

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
