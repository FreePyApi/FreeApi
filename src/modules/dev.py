# Dev
# Maintainer(s): SzaBee13
# Contributor(s): SzaBee13
# Reviewer(s): SzaBee13
import re
import json
import difflib
import random as rand
from pathlib import Path

DATA_FILE_DEV_REGEX = Path(__file__).parent.parent / "assets" / "dev" / "regex.json"
DATA_FILE_DEV_DEBUG = Path(__file__).parent.parent / "assets" / "dev" / "debug.json"

def _load_json_asset(path, default=None):
  try:
    with open(path, "r") as f:
      return json.load(f)
  except Exception:
    return default

_JSON_ASSETS = _load_json_asset(DATA_FILE_DEV_REGEX, {})
MAPPINGS = _JSON_ASSETS.get("mappings", {}) if isinstance(_JSON_ASSETS, dict) else {}

_DEBUG_ASSETS = _load_json_asset(DATA_FILE_DEV_DEBUG, {})
FUNNY_RESPONSES = _DEBUG_ASSETS.get("responses", []) if isinstance(_DEBUG_ASSETS, dict) else {}
DOCS = _DEBUG_ASSETS.get("docs", {}) if isinstance(_DEBUG_ASSETS, dict) else {}

## REGEX
def test_regex(pattern: str, test_string: str) -> dict:
  """Tests a regex pattern against a test string and returns the results.

  Args:
    pattern: The regex pattern to test.
    test_string: The string to test the pattern against.
  Returns:
    A dictionary containing the results of the regex test, including:
      - matches: A list of all matches found in the test string.
      - match_count: The total number of matches found.
      - pattern: The regex pattern that was tested.
      - test_string: The original test string.
  """
  matches = re.findall(pattern, test_string)
  return {
    "matches": matches,
    "match_count": len(matches),
    "pattern": pattern,
    "test_string": test_string
  }

def generate_regex(human_readable_pattern: dict) -> dict:
  regex_pattern = ""
  for key, value in human_readable_pattern.items():
    if key in MAPPINGS:
      regex_pattern += MAPPINGS[key]
    else:
      regex_pattern += re.escape(value)
  return {
    "regex_pattern": regex_pattern,
    "human_readable_pattern": human_readable_pattern
  }

def get_regex_mappings() -> dict:
  """Returns the current regex mappings.

  Returns:
    A dictionary containing the current regex mappings, where each key is a human-readable description and each value is the corresponding regex pattern.
  """
  return MAPPINGS

## Json
def validate_json(json_string: str) -> dict:
  """Validates a JSON string and returns the results.

  Args:
    json_string: The JSON string to validate.
  Returns:
    A dictionary containing the results of the JSON validation, including:
      - is_valid: A boolean indicating whether the JSON string is valid or not.
      - error_message: An error message if the JSON string is invalid, otherwise None.
      - json_string: The original JSON string that was validated.
  """
  try:
    json.loads(json_string)
    return {
      "is_valid": True,
      "error_message": None,
      "json_string": json_string
    }
  except json.JSONDecodeError as e:
    return {
      "is_valid": False,
      "error_message": str(e),
      "json_string": json_string
    }

def prettify_json(json_string: str, indent: int = 4) -> dict:
  """Prettifies a JSON string and returns the results.

  Args:
    json_string: The JSON string to prettify.
    indent: The number of spaces to use for indentation.
  Returns:
    A dictionary containing the results of the JSON prettification, including:
      - prettified_json: The prettified JSON string if the input is valid, otherwise None.
      - error_message: An error message if the JSON string is invalid, otherwise None.
      - json_string: The original JSON string that was prettified.
  """
  try:
    parsed_json = json.loads(json_string)
    prettified_json = json.dumps(parsed_json, indent=indent)
    return {
      "prettified_json": prettified_json,
      "error_message": None,
      "json_string": json_string
    }
  except json.JSONDecodeError as e:
    return {
      "prettified_json": None,
      "error_message": str(e),
      "json_string": json_string
    }

## Other
def generate_diff(old_string: str, new_string: str) -> dict:
  """Generates a diff between two strings and returns the results.

  Args:
    old_string: The original string.
    new_string: The modified string.
  Returns:
    A dictionary containing the results of the diff generation, including:
      - diff: A list of differences between the two strings.
      - old_string: The original string that was compared.
      - new_string: The modified string that was compared.
  """
  diff = list(difflib.unified_diff(old_string.splitlines(), new_string.splitlines(), lineterm=''))
  return {
    "diff": diff,
    "old_string": old_string,
    "new_string": new_string
  }

def help_me_debug(what_to_debug: str) -> dict:
  """Provides a humorous response to the user asking for help with debugging.

  Args:
    what_to_debug: A description of what the user is trying to debug.
  Returns:
    A dictionary containing a humorous message encouraging the user to debug their code.
  """
  if FUNNY_RESPONSES:
    response = rand.choice(FUNNY_RESPONSES)
  else:
    response = "Have you tried turning it off and on again?"

  return {
    "message": response,
    "docs": DOCS.get(what_to_debug, "No documentation available for this topic.") if isinstance(DOCS, dict) else "No documentation available."
  }
  