# Text
# Maintainer(s): SzaBee13
# Contributor(s): SzaBee13

## Counting
def count_words(text: str) -> dict:
  """Counts the number of words in a given text."""
  return { "words": len(text.split()) }

def count_characters(text: str) -> dict:
  """Counts the number of characters in a given text."""
  return { "characters": len(text.replace(" ", "").replace("\n", "").replace("\t", "")) }

def count_sentences(text: str) -> dict:
  """Counts the number of sentences in a given text."""
  return { "sentences": len(text.split('.')) }

def count_paragraphs(text: str) -> dict:
  """Counts the number of paragraphs in a given text."""
  return { "paragraphs": len(text.split('\n\n')) }

def count(text: str) -> dict:
  """Counts words, characters, sentences, and paragraphs in a given text."""
  return {
    "words": count_words(text),
    "characters": count_characters(text),
    "sentences": count_sentences(text),
    "paragraphs": count_paragraphs(text)
  }

## Password
# DATA DISCLAIMER
# WE DO NOT STORE ANY PASSWORDS. ALL PASSWORDS ARE PROCESSED IN-MEMORY AND NEVER LOGGED OR STORED IN ANY WAY. THIS MODULE IS FOR EVALUATION AND GENERATION PURPOSES ONLY. USE WITH CAUTION AND NEVER INPUT REAL PASSWORDS.
import random
import string

def password_strength(password: str) -> dict:
  """Evaluates the strength of a given password."""
  import re

  strength = 0
  if len(password) >= 8:
    strength += 1
  if re.search(r'[A-Z]', password):
    strength += 1
  if re.search(r'[a-z]', password):
    strength += 1
  if re.search(r'[0-9]', password):
    strength += 1
  if re.search(r'[@$!%*?&]', password):
    strength += 1

  return { "strength": strength, "length": len(password) }
    
def generate_password(length: int = 12, charset: str = None) -> dict:
  """Generates a random password of a given length."""

  if charset is None:
    characters = string.ascii_letters + string.digits + string.punctuation
  else:
    characters = charset
  password = ''.join(random.choice(characters) for _ in range(length))
  return { "password": password, "strength": password_strength(password)["strength"] }

def password_disclaimer() -> dict:
  """Returns a disclaimer about password handling."""
  return {
    "disclaimer": "WE DO NOT STORE ANY PASSWORDS. ALL PASSWORDS ARE PROCESSED IN-MEMORY AND NEVER LOGGED OR STORED IN ANY WAY. THIS MODULE IS FOR EVALUATION AND GENERATION PURPOSES ONLY. USE WITH CAUTION AND NEVER INPUT REAL PASSWORDS."
  }

## Formatting
import re

def slugify(text: str) -> dict:
  """Converts a given text into a URL-friendly slug."""
  slug = re.sub(r'[\W_]+', '-', text.lower()).strip('-')
  return { "slug": slug }

def camel_case(text: str) -> dict:
  """Converts a given text into camelCase."""
  words = re.split(r'[\W_]+', text)
  camel = words[0].lower() + ''.join(word.capitalize() for word in words[1:])
  return { "camelCase": camel }

def snake_case(text: str) -> dict:
  """Converts a given text into snake_case."""
  snake = re.sub(r'[\W]+', '_', text.lower()).strip('_')
  return { "snake_case": snake }

def pascal_case(text: str) -> dict:
  """Converts a given text into PascalCase."""
  words = re.split(r'[\W_]+', text)
  pascal = ''.join(word.capitalize() for word in words)
  return { "pascal_case": pascal }

## Other

def lorem_ipsum(length: int = 100) -> dict:
  """Generates a Lorem Ipsum placeholder text of a given length."""
  lorem = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
  return { "lorem_ipsum": (lorem * (length // len(lorem) + 1))[:length] }

def random_string(length: int = 12, charset: str = None) -> dict:
  """Generates a random string of a given length."""
  if charset is None:
    characters = string.ascii_letters + string.digits
  else:
    characters = charset
  random_str = ''.join(random.choice(characters) for _ in range(length))
  return { "random_string": random_str }