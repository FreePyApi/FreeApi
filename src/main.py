from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
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

# TEXT
from .modules import text

## Counting
@app.post("/text/count", tags=["Text", "Counting"])
def text_count(text: str):
    return text.count(text)

@app.post("/text/count/words", tags=["Text", "Counting"])
def text_count_words(text: str):
    return text.count_words(text)

@app.post("/text/count/characters", tags=["Text", "Counting"])
def text_count_characters(text: str):
    return text.count_characters(text)

@app.post("/text/count/sentences", tags=["Text", "Counting"])
def text_count_sentences(text: str):
    return text.count_sentences(text)

@app.post("/text/count/paragraphs", tags=["Text", "Counting"])
def text_count_paragraphs(text: str):
    return text.count_paragraphs(text)

## Password
@app.post("/text/password/strength", tags=["Text", "Password"])
def text_password_strength(password: str):
    return text.password_strength(password)

@app.post("/text/password/generate", tags=["Text", "Password"])
def text_password_generate(length: int = 12, charset: str = None):
    return text.generate_password(length=length, charset=charset)

@app.get("/text/password/disclaimer", tags=["Text", "Password"])
def text_password_disclaimer():
    return text.password_disclaimer()

# TIME AND DATE
from .modules import datetime
from time import time

@app.get("/datetime/unix_timestamp", tags=["Date", "Time"])
def get_unix_timestamp():
    return datetime.unix_timestamp()

@app.get("/datetime/format", tags=["Date", "Time"])
def format_time(timestamp: int = int(time()), format: str = "%Y-%m-%d %H:%M:%S", timezone: str = "UTC"):
    return datetime.format_time(timestamp, format, timezone)

@app.get("/datetime/timezones", tags=["Date", "Time"])
def get_timezones():
    return datetime.get_timezones()

@app.get("/datetime/convert_timezone", tags=["Date", "Time"])
def convert_timezone(timestamp: int = int(time()), from_tz: str = "UTC", to_tz: str = "UTC"):
    return datetime.convert_timezone(timestamp, from_tz, to_tz)

@app.get("/datetime/time_difference", tags=["Date", "Time"])
def time_difference(timestamp1: int, timestamp2: int):
    return datetime.time_difference(timestamp1, timestamp2)

@app.get("/datetime/is_leap_year", tags=["Date", "Time"])
def is_leap_year(year: int):
    return datetime.is_leap_year(year)

@app.get("/datetime/day_of_week", tags=["Date", "Time"])
def day_of_week(timestamp: int = int(time()), timezone: str = "UTC"):
    return datetime.day_of_week(timestamp, timezone)

@app.get("/datetime/summer_time", tags=["Date", "Time"])
def summer_time(timestamp: int = int(time()), timezone: str = "UTC"):
    return datetime.summer_time(timestamp, timezone)