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

def validate_uuid(uuid_string: str) -> dict:
  """Validates if a given string is a valid UUID."""
  try:
    val = uuid.UUID(uuid_string, version=4)
    return { "is_valid": True }
  except ValueError:
    return { "is_valid": False }

def decode_uuid(uuid_string: str) -> dict:
  """Decodes a UUID string into its components."""
  try:
    val = uuid.UUID(uuid_string)
    return {
      "hex": val.hex,
      "int": val.int,
      "version": val.version,
      "variant": val.variant,
      "fields": val.fields,
      "time_low": val.time_low,
      "time_mid": val.time_mid,
      "time_hi_version": val.time_hi_version,
      "clock_seq_hi_variant": val.clock_seq_hi_variant,
      "clock_seq_low": val.clock_seq_low,
      "node": val.node
    }
  except ValueError:
    return { "error": "Invalid UUID string." }

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