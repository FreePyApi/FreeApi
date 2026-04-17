from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
# from pydantic import BaseModel
from pathlib import Path

app = FastAPI(
  title="FreeAPI",
  description="A Free and open source api for everyone.",
  version="1.0.0",
  docs_url="/docs",
  redoc_url="/redoc",
  openapi_url="/openapi.json",
)

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"

# Expose static assets so favicon and other files are publicly reachable.
app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")


@app.get("/favicon.ico", include_in_schema=False)
def favicon_ico():
  return FileResponse(ASSETS_DIR / "favicon.png")


@app.get("/favicon.svg", include_in_schema=False)
def favicon_svg():
  return FileResponse(ASSETS_DIR / "favicon.svg")

@app.get("/status", tags=["Status"])
def get_status():
  return {"status": "running"}

# Organization
@app.get("/github", tags=["Organization"])
def get_github():
  return {"github_repo": "https://github.com/FreePyApi/FreeApi", "github_organization": "https://github.com/FreePyApi" }

#####################
# TEXT
#####################
from .modules import text as mtext # We give modules an M prefix

# Counting
@app.post("/text/count", tags=["Text/Counting"])
def text_count(text: str):
  return mtext.count(text)

@app.post("/text/count/words", tags=["Text/Counting"])
def text_count_words(text: str):
  return mtext.count_words(text)

@app.post("/text/count/characters", tags=["Text/Counting"])
def text_count_characters(text: str):
  return mtext.count_characters(text)

@app.post("/text/count/sentences", tags=["Text/Counting"])
def text_count_sentences(text: str):
  return mtext.count_sentences(text)

@app.post("/text/count/paragraphs", tags=["Text/Counting"])
def text_count_paragraphs(text: str):
  return mtext.count_paragraphs(text)

# Password
@app.post("/text/password/strength", tags=["Text/Password"])
def text_password_strength(password: str):
  return mtext.password_strength(password)

@app.post("/text/password/generate", tags=["Text/Password"])
def text_password_generate(length: int = 12, charset: str = None):
  return mtext.generate_password(length=length, charset=charset)

@app.get("/text/password/disclaimer", tags=["Text/Password"])
def text_password_disclaimer():
  return mtext.password_disclaimer()

# Formatting
@app.post("/text/formatting/slugify", tags="Text/Formatting")
def text_format_slugify(text: str):
  return mtext.slugify(text=text)

@app.post("/text/formatting/camel_case", tags="Text/Formatting")
def text_camel_case(text: str):
  return mtext.camel_case(text=text)

@app.post("/text/formatting/pascal_case", tags="Text/Formatting")
def text_pascal_case(text: str):
  return mtext.pascal_case(text=text)

@app.post("/text/formatting/camel_case", tags="Text/Formatting")
def text_camel_case(text: str):
  return mtext.camel_case(text=text)

# Other
@app.get("/text/lorem_ipsum/{length}", tags="Text/Other")
def text_lorem_ipsum(length: str):
  return mtext.lorem_ipsum(length=length)

#####################
# DateTime
#####################
from .modules import datetime as mdatetime
from time import time

@app.get("/datetime/unix_timestamp", tags=["DateTime"])
def get_unix_timestamp():
  return mdatetime.unix_timestamp()

@app.get("/datetime/format", tags=["DateTime"])
def format_time(timestamp: int = int(time()), format: str = "%Y-%m-%d %H:%M:%S", timezone: str = "UTC"):
  return mdatetime.format_time(timestamp, format, timezone)

@app.get("/datetime/timezones", tags=["DateTime"])
def get_timezones():
  return mdatetime.get_timezones()

@app.get("/datetime/convert_timezone", tags=["DateTime"])
def convert_timezone(timestamp: int = int(time()), from_tz: str = "UTC", to_tz: str = "UTC"):
  return mdatetime.convert_timezone(timestamp, from_tz, to_tz)

@app.get("/datetime/time_difference", tags=["DateTime"])
def time_difference(timestamp1: int, timestamp2: int):
  return mdatetime.time_difference(timestamp1, timestamp2)

@app.get("/datetime/is_leap_year", tags=["DateTime"])
def is_leap_year(year: int):
  return mdatetime.is_leap_year(year)

@app.get("/datetime/day_of_week", tags=["DateTime"])
def day_of_week(timestamp: int = int(time()), timezone: str = "UTC"):
  return mdatetime.day_of_week(timestamp, timezone)

@app.get("/datetime/summer_time", tags=["DateTime"])
def summer_time(timestamp: int = int(time()), timezone: str = "UTC"):
  return mdatetime.summer_time(timestamp, timezone)

#####################
# Geo
#####################
from .modules import geo as mgeo

@app.post("/geo/geocode", tags=["Geo"])
def geo_geocode(address: str):
  return mgeo.geocode(address=address)

@app.post("/geo/is_sea", tags=["Geo"])
def geo_is_sea(latitude: float, longitude: float):
  return mgeo.is_sea(latitude=latitude, longitude=longitude)

@app.post("/geo/get_timezone", tags=["Geo"])
def geo_get_tz(latitude: float, longitude: float):
  return mgeo.get_timezone(latitude=latitude, longitude=longitude)

@app.post("/geo/get_address", tags=["Geo"])
def geo_get_addr(latitude: float, longitude: float):
  return mgeo.get_address(latitude=latitude, longitude=longitude)

#####################
# UUID and Hashing
#####################
from .modules import uuid_hashing as muuid_hashing
@app.get("/uuid/generate/{version}", tags=["UUID and Hashing"])
def uuid_generate(version: int):
  return muuid_hashing.generate_uuid(version=version)

@app.get("/uuid/validate", tags=["UUID and Hashing"])
def uuid_validate(uuid_string: str):
  return muuid_hashing.validate_uuid(uuid_string=uuid_string)

@app.get("/uuid/decode", tags=["UUID and Hashing"])
def uuid_decode(uuid_string: str):
  return muuid_hashing.decode_uuid(uuid_string=uuid_string)

@app.post("/hash/string", tags=["UUID and Hashing"])
def hash_string(text: str, algorithm: str = "sha256"):
  return muuid_hashing.hash_string(text=text, algorithm=algorithm)

@app.post("/hash/base64_encode", tags=["UUID and Hashing"])
def base64_encode(text: str):
  return muuid_hashing.base64_encode(text=text)

@app.post("/hash/base64_decode", tags=["UUID and Hashing"])
def base64_decode(encoded_text: str):
  return muuid_hashing.base64_decode(encoded_text=encoded_text)

#####################
# Math
#####################
from .modules import math as mmath

@app.post("/math/convert_units", tags=["Math"])
def convert_units(value: float, conversion_type: str):
  return mmath.convert_units(value=value, conversion_type=conversion_type)

@app.get("/math/conversion_types", tags=["Math"])
def get_conversion_types():
  return mmath.get_conversion_types()

@app.get("/math/check/prime", tags=["Math"])
def check_prime(number: int):
  return mmath.check_prime(number=number)

@app.get("/math/check/odd_even", tags=["Math"])
def check_odd_even(number: int):
  return mmath.check_odd_even(number=number)

@app.get("/math/factorial", tags=["Math"])
def factorial(n: int):
  return mmath.factorial(n=n)

@app.get("/math/random_number", tags=["Math"])
def random_number(min: int = 0, max: int = 100):
  return mmath.random_number(min=min, max=max)

@app.get("/math/fibonacci", tags=["Math"])
def fibonacci(n: int):
  return mmath.fibonacci(n=n)