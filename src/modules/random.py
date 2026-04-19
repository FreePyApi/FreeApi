# Random
# Maintainer(s): SzaBee13
# Contributor(s): SzaBee13
# Asset Contributor(s): Sv443 (Jokes) https://git.sv443.net/Sv443/JokeAPI-v2, dwyl (Quotes) https://github.com/dwyl/quotes, SSA (First names) https://www.ssa.gov/oact/babynames/decades/century.html, ThoughtCo (Last names) https://www.thoughtco.com/most-common-us-surnames-1422656, ChatGPT (dad jokes) 💀
# Reviewer(s): SzaBee13
import random as rand
import json
from pathlib import Path
from .math import convert_numeric_system as cns
from ..config import settings
from numpy import gradient

DATA_FILE_QUOTES = Path(__file__).parent.parent / "assets" / "random" / "quotes.json"
try:
  with open(DATA_FILE_QUOTES, "r") as f:
    _DATA = json.load(f)
    QUOTES = _DATA if isinstance(_DATA, list) else []
except Exception:
  QUOTES = []

DATA_FILE_JOKES = Path(__file__).parent.parent / "assets" / "random" / "jokes.json"
try:
  with open(DATA_FILE_JOKES, "r") as f:
    _DATA = json.load(f)
    JOKES = _DATA.get("jokes", []) if isinstance(_DATA, dict) else []
except Exception:
  JOKES = []

DATA_FILE_DAD_JOKES = Path(__file__).parent.parent / "assets" / "random" / "dad_jokes.json"
try:
  with open(DATA_FILE_DAD_JOKES, "r") as f:
    _DATA = json.load(f)
    DAD_JOKES = _DATA.get("jokes", []) if isinstance(_DATA, dict) else []
except Exception:
  DAD_JOKES = []

def random_color() -> dict:
  COLOR = (rand.randint(0,255), rand.randint(0,255), rand.randint(0,255))
  HEX = f"#{cns('decimal', 'hexadecimal', COLOR[0])['result']}{cns('decimal', 'hexadecimal', COLOR[1])['result']}{cns('decimal', 'hexadecimal', COLOR[2])['result']}"
  GOOGLE_COLOR_PICKER_URL = f"https://google.com/search?q={HEX.replace('#', '%23')}&utm_source={settings.freeapi_domain}"
  return { "hex": HEX, "rgb": COLOR, "google": GOOGLE_COLOR_PICKER_URL}

def random_gradient(colors: int = 2, type: str = "linear") -> dict:
  if type not in ["linear", "radial"]:
    return {"error": "Unsupported gradient type. Supported types are 'linear' and 'radial'.", "code": 400}
  
  if colors < 2:
    return {"error": "At least two colors are required to create a gradient.", "code": 400}
  
  color_list = [random_color() for _ in range(colors)]
  
  if type == "linear":
    gradient_str = f"linear-gradient({', '.join([color['hex'] for color in color_list])})"
  elif type == "radial":
    gradient_str = f"radial-gradient({', '.join([color['hex'] for color in color_list])})"
  else:
    return {"error": "Unsupported gradient type. Supported types are 'linear' and 'radial'.", "code": 400}
  
  return {
    "type": type,
    "colors": color_list,
    "gradient": gradient_str
  }

def random_quote(tag: str = None) -> dict:
  if not QUOTES:
    return {"error": "No quotes available.", "code": 500}
  
  if tag:
    filtered_quotes = [quote for quote in QUOTES if tag in quote.get("tags", [])]
    if not filtered_quotes:
      return {"error": f"No quotes found with the tag '{tag}'.", "code": 404}
    quote = rand.choice(filtered_quotes)
  else:
    quote = rand.choice(QUOTES)
  
  return {
    "quote": quote.get("text"),
    "author": quote.get("author"),
    "tags": quote.get("tags", []),
    "source": quote.get("source", "Unknown")
  }

def random_joke(category: str = None, explicit: dict = {"nsfw": False, "religious": False, "political": False, "racist": False, "sexist": False, "explicit": False}) -> dict:
  if not JOKES:
    return {"error": "No jokes available.", "code": 500}
  
  filtered_jokes = JOKES
  
  if category:
    filtered_jokes = [joke for joke in filtered_jokes if joke.get("category", "").lower() == category.lower()]
  
  for key, value in explicit.items():
    if not value:
      filtered_jokes = [joke for joke in filtered_jokes if not joke.get(key, False)]
  
  if not filtered_jokes:
    return {"error": "No jokes found matching the specified criteria.", "code": 404}
  
  joke = rand.choice(filtered_jokes)
  # Return a consistent shape: single-type jokes have a `joke` field,
  # twopart-type jokes have `setup` and `delivery`.
  if joke.get("type") == "single":
    return {
      "category": joke.get("category"),
      "type": joke.get("type"),
      "joke": joke.get("joke"),
      "setup": None,
      "delivery": None,
      "flags": {key: joke.get(key, False) for key in explicit.keys()}
    }

  return {
    "category": joke.get("category"),
    "type": joke.get("type"),
    "joke": " ".join(part for part in (joke.get("setup"), joke.get("delivery")) if part),
    "setup": joke.get("setup"),
    "delivery": joke.get("delivery"),
    "flags": {key: joke.get(key, False) for key in explicit.keys()}
  }


def random_dad_joke(category: str = None) -> dict:
  if not DAD_JOKES:
    return {"error": "No dad jokes available.", "code": 500}

  filtered_jokes = DAD_JOKES

  if category:
    filtered_jokes = [joke for joke in filtered_jokes if joke.get("category", "").lower() == category.lower()]

  if not filtered_jokes:
    return {"error": f"No dad jokes found with the category '{category}'.", "code": 404}

  joke = rand.choice(filtered_jokes)

  return {
    "category": joke.get("category"),
    "type": joke.get("type"),
    "setup": joke.get("setup"),
    "delivery": joke.get("delivery")
  }
