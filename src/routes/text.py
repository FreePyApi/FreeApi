from typing import Any, Optional

from fastapi import APIRouter, Body, Query, Path as ParamPath

from ..modules import text as mtext

router = APIRouter()


@router.post("/text/count", tags=["Text/Counting"])
def text_count(text: str = Body(..., min_length=1, max_length=10000)) -> dict[str, Any]:
  return mtext.count(text)


@router.post("/text/count/words", tags=["Text/Counting"])
def text_count_words(text: str = Body(..., min_length=1, max_length=10000)) -> dict[str, Any]:
  return mtext.count_words(text)


@router.post("/text/count/characters", tags=["Text/Counting"])
def text_count_characters(text: str = Body(..., min_length=1, max_length=10000)) -> dict[str, Any]:
  return mtext.count_characters(text)


@router.post("/text/count/sentences", tags=["Text/Counting"])
def text_count_sentences(text: str = Body(..., min_length=1, max_length=10000)) -> dict[str, Any]:
  return mtext.count_sentences(text)


@router.post("/text/count/paragraphs", tags=["Text/Counting"])
def text_count_paragraphs(text: str = Body(..., min_length=1, max_length=10000)) -> dict[str, Any]:
  return mtext.count_paragraphs(text)


@router.post("/text/password/strength", tags=["Text/Password"])
def text_password_strength(password: str = Body(..., embed=True, min_length=4, max_length=1024)) -> dict[str, Any]:
  return mtext.password_strength(password)


@router.post("/text/password/generate", tags=["Text/Password"])
def text_password_generate(length: int = Query(12, ge=4, le=256), charset: Optional[str] = Query(None, max_length=500)) -> dict[str, Any]:
  return mtext.generate_password(length=length, charset=charset)


@router.get("/text/password/disclaimer", tags=["Text/Password"])
def text_password_disclaimer() -> dict[str, Any]:
  return mtext.password_disclaimer()


@router.post("/text/formatting/slugify", tags=["Text/Formatting"])
def text_format_slugify(text: str = Body(..., min_length=1, max_length=2000)) -> dict[str, Any]:
  return mtext.slugify(text=text)


@router.post("/text/formatting/camel_case", tags=["Text/Formatting"])
def text_camel_case(text: str = Body(..., min_length=1, max_length=2000)) -> dict[str, Any]:
  return mtext.camel_case(text=text)


@router.post("/text/formatting/pascal_case", tags=["Text/Formatting"])
def text_pascal_case(text: str = Body(..., min_length=1, max_length=2000)) -> dict[str, Any]:
  return mtext.pascal_case(text=text)


@router.get("/text/lorem_ipsum/{length}", tags=["Text/Other"])
def text_lorem_ipsum(length: int = ParamPath(..., ge=1, le=1000)) -> dict[str, Any]:
  return mtext.lorem_ipsum(length=length)
