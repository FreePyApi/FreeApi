# UUID and Hashing
# Maintainer(s): SzaBee13
# Contributor(s): SzaBee13
import uuid
import hashlib

def generate_uuid(version: int) -> dict:
  """Generates a random UUID."""
  if version == 4:
    return { "uuid": str(uuid.uuid4()) }
  elif version == 7:
    return { "uuid": str(uuid.uuid7()) }
  else:
    return { "error": "Unsupported UUID version. Use 4 or 7." }

def hash_string(text: str, algorithm: str = "sha256") -> dict:
  """Hashes a given string using the specified algorithm."""
  if algorithm == "md5":
    hashed = hashlib.md5(text.encode()).hexdigest()
  elif algorithm == "sha1":
    hashed = hashlib.sha1(text.encode()).hexdigest()
  elif algorithm == "sha256":
    hashed = hashlib.sha256(text.encode()).hexdigest()
  else:
    return { "error": "Unsupported hashing algorithm. Use md5, sha1, or sha256." }
  
  return { "hashed": hashed }

def base64_encode(text: str) -> dict:
  """Encodes a given string into Base64."""
  encoded = text.encode('utf-8').hex()
  return { "base64_encoded": encoded }

def base64_decode(encoded_text: str) -> dict:
  """Decodes a given Base64 string."""
  try:
    decoded = bytes.fromhex(encoded_text).decode('utf-8')
    return { "base64_decoded": decoded }
  except Exception as e:
    return { "error": f"Invalid Base64 string: {str(e)}" }