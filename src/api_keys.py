from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

try:
  from argon2 import PasswordHasher
  from argon2.exceptions import InvalidHash, VerificationError, VerifyMismatchError
  HAS_ARGON2 = True
except ImportError:  # pragma: no cover - fallback for lean local environments
  PasswordHasher = None
  InvalidHash = VerificationError = VerifyMismatchError = Exception
  HAS_ARGON2 = False

from fastapi import HTTPException, status

from .config import settings

API_KEY_PREFIX = "fpk"
MAX_API_KEYS_PER_USER = 5
PASSWORD_HASHER = PasswordHasher() if HAS_ARGON2 else None


@dataclass(frozen=True)
class ApiKeyRecord:
  key_uuid: uuid.UUID
  user_identifier: str
  user_data: dict[str, Any]
  key_hash: str
  description: Optional[str]
  created_at: datetime
  expires_at: Optional[datetime]
  last_used_at: Optional[datetime]

  def to_public_dict(self) -> dict[str, Any]:
    active = self.expires_at is None or self.expires_at > datetime.now(timezone.utc)
    return {
      "uuid": str(self.key_uuid),
      "description": self.description,
      "created_at": self.created_at,
      "expires_at": self.expires_at,
      "last_used_at": self.last_used_at,
      "active": active,
    }


class BaseApiKeyStore:
  def ensure_schema(self) -> None:
    raise NotImplementedError

  def create_api_key(self, user: dict[str, Any], description: Optional[str], expires_at: Optional[datetime]) -> tuple[str, ApiKeyRecord]:
    raise NotImplementedError

  def list_api_keys(self, user: dict[str, Any]) -> list[ApiKeyRecord]:
    raise NotImplementedError

  def delete_api_key(self, user: dict[str, Any], key_uuid: uuid.UUID) -> bool:
    raise NotImplementedError

  def authenticate_api_key(self, raw_token: str) -> Optional[dict[str, Any]]:
    raise NotImplementedError


class MemoryApiKeyStore(BaseApiKeyStore):
  def __init__(self) -> None:
    self._records: dict[uuid.UUID, ApiKeyRecord] = {}

  def ensure_schema(self) -> None:
    return None

  def create_api_key(self, user: dict[str, Any], description: Optional[str], expires_at: Optional[datetime]) -> tuple[str, ApiKeyRecord]:
    user_identifier = _user_identifier(user)
    self._cleanup_expired()
    active_key_count = sum(1 for record in self._records.values() if record.user_identifier == user_identifier and _is_active(record.expires_at))
    if active_key_count >= MAX_API_KEYS_PER_USER:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum number of API keys reached")

    key_uuid = uuid.uuid4()
    raw_token = _build_raw_token(key_uuid)
    record = ApiKeyRecord(
      key_uuid=key_uuid,
      user_identifier=user_identifier,
      user_data=dict(user),
      key_hash=_hash_secret(_extract_secret(raw_token)),
      description=description,
      created_at=datetime.now(timezone.utc),
      expires_at=_normalize_datetime(expires_at),
      last_used_at=None,
    )
    self._records[key_uuid] = record
    return raw_token, record

  def list_api_keys(self, user: dict[str, Any]) -> list[ApiKeyRecord]:
    user_identifier = _user_identifier(user)
    self._cleanup_expired()
    return [record for record in self._records.values() if record.user_identifier == user_identifier]

  def delete_api_key(self, user: dict[str, Any], key_uuid: uuid.UUID) -> bool:
    user_identifier = _user_identifier(user)
    record = self._records.get(key_uuid)
    if record is None or record.user_identifier != user_identifier:
      return False
    del self._records[key_uuid]
    return True

  def authenticate_api_key(self, raw_token: str) -> Optional[dict[str, Any]]:
    try:
      key_uuid, secret = _parse_raw_token(raw_token)
    except ValueError:
      return None

    record = self._records.get(key_uuid)
    if record is None or not _is_active(record.expires_at):
      return None

    if not _verify_secret(record.key_hash, secret):
      return None

    self._records[key_uuid] = ApiKeyRecord(
      key_uuid=record.key_uuid,
      user_identifier=record.user_identifier,
      user_data=record.user_data,
      key_hash=record.key_hash,
      description=record.description,
      created_at=record.created_at,
      expires_at=record.expires_at,
      last_used_at=datetime.now(timezone.utc),
    )
    return dict(record.user_data)

  def _cleanup_expired(self) -> None:
    expired_keys = [key_uuid for key_uuid, record in self._records.items() if record.expires_at is not None and record.expires_at <= datetime.now(timezone.utc)]
    for key_uuid in expired_keys:
      del self._records[key_uuid]


class PostgresApiKeyStore(BaseApiKeyStore):
  def __init__(self, dsn: str) -> None:
    self.dsn = dsn
    self._schema_ready = False

  def ensure_schema(self) -> None:
    if self._schema_ready:
      return

    import psycopg

    with psycopg.connect(self.dsn) as conn:
      with conn.cursor() as cursor:
        cursor.execute(
          """
          CREATE TABLE IF NOT EXISTS api_keys (
            key_uuid UUID PRIMARY KEY,
            user_identifier TEXT NOT NULL,
            user_data JSONB NOT NULL,
            key_hash TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at TIMESTAMPTZ,
            last_used_at TIMESTAMPTZ
          )
          """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS api_keys_user_identifier_idx ON api_keys (user_identifier)")
      conn.commit()

    self._schema_ready = True

  def create_api_key(self, user: dict[str, Any], description: Optional[str], expires_at: Optional[datetime]) -> tuple[str, ApiKeyRecord]:
    import psycopg
    from psycopg.types.json import Jsonb

    self.ensure_schema()
    user_identifier = _user_identifier(user)
    normalized_expires_at = _normalize_datetime(expires_at)
    if normalized_expires_at is not None and normalized_expires_at <= datetime.now(timezone.utc):
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expiration date must be in the future")

    with psycopg.connect(self.dsn) as conn:
      with conn.cursor() as cursor:
        cursor.execute(
          """
          SELECT COUNT(*)
          FROM api_keys
          WHERE user_identifier = %s
            AND (expires_at IS NULL OR expires_at > NOW())
          """,
          (user_identifier,),
        )
        active_key_count = int(cursor.fetchone()[0] or 0)
        if active_key_count >= MAX_API_KEYS_PER_USER:
          raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum number of API keys reached")

        key_uuid = uuid.uuid4()
        raw_token = _build_raw_token(key_uuid)
        secret = _extract_secret(raw_token)
        key_hash = _hash_secret(secret)
        created_at = datetime.now(timezone.utc)
        cursor.execute(
          """
          INSERT INTO api_keys (key_uuid, user_identifier, user_data, key_hash, description, created_at, expires_at)
          VALUES (%s, %s, %s, %s, %s, %s, %s)
          """,
          (key_uuid, user_identifier, Jsonb(dict(user)), key_hash, description, created_at, normalized_expires_at),
        )
        conn.commit()

    return raw_token, ApiKeyRecord(
      key_uuid=key_uuid,
      user_identifier=user_identifier,
      user_data=dict(user),
      key_hash=key_hash,
      description=description,
      created_at=created_at,
      expires_at=normalized_expires_at,
      last_used_at=None,
    )

  def list_api_keys(self, user: dict[str, Any]) -> list[ApiKeyRecord]:
    import psycopg

    self.ensure_schema()
    user_identifier = _user_identifier(user)
    with psycopg.connect(self.dsn) as conn:
      with conn.cursor() as cursor:
        cursor.execute(
          """
          SELECT key_uuid, user_identifier, user_data, key_hash, description, created_at, expires_at, last_used_at
          FROM api_keys
          WHERE user_identifier = %s
          ORDER BY created_at DESC
          """,
          (user_identifier,),
        )
        rows = cursor.fetchall()

    return [_row_to_record(row) for row in rows]

  def delete_api_key(self, user: dict[str, Any], key_uuid: uuid.UUID) -> bool:
    import psycopg

    self.ensure_schema()
    user_identifier = _user_identifier(user)
    with psycopg.connect(self.dsn) as conn:
      with conn.cursor() as cursor:
        cursor.execute(
          "DELETE FROM api_keys WHERE key_uuid = %s AND user_identifier = %s RETURNING key_uuid",
          (key_uuid, user_identifier),
        )
        deleted = cursor.fetchone() is not None
        conn.commit()
    return deleted

  def authenticate_api_key(self, raw_token: str) -> Optional[dict[str, Any]]:
    import psycopg

    try:
      key_uuid, secret = _parse_raw_token(raw_token)
    except ValueError:
      return None

    self.ensure_schema()
    with psycopg.connect(self.dsn) as conn:
      with conn.cursor() as cursor:
        cursor.execute(
          """
          SELECT key_uuid, user_identifier, user_data, key_hash, description, created_at, expires_at, last_used_at
          FROM api_keys
          WHERE key_uuid = %s
          """,
          (key_uuid,),
        )
        row = cursor.fetchone()
        if row is None:
          return None

        record = _row_to_record(row)
        if not _is_active(record.expires_at):
          return None
        if not _verify_secret(record.key_hash, secret):
          return None

        cursor.execute(
          "UPDATE api_keys SET last_used_at = NOW() WHERE key_uuid = %s",
          (key_uuid,),
        )
        conn.commit()
        return dict(record.user_data)


_STORE: BaseApiKeyStore | None = None


def get_api_key_store() -> BaseApiKeyStore:
  global _STORE
  if _STORE is not None:
    return _STORE

  if settings.postgres_url:
    _STORE = PostgresApiKeyStore(settings.postgres_url)
  else:
    _STORE = MemoryApiKeyStore()
  _STORE.ensure_schema()
  return _STORE


def is_api_key_auth_enabled() -> bool:
  return bool(settings.postgres_url or isinstance(get_api_key_store(), MemoryApiKeyStore))


def create_api_key(user: dict[str, Any], description: Optional[str], expires_at: Optional[datetime]) -> dict[str, Any]:
  raw_token, record = get_api_key_store().create_api_key(user, description, expires_at)
  return {
    "api_key": raw_token,
    "key": record.to_public_dict(),
  }


def list_api_keys(user: dict[str, Any]) -> dict[str, Any]:
  records = get_api_key_store().list_api_keys(user)
  return {"keys": [record.to_public_dict() for record in records]}


def delete_api_key(user: dict[str, Any], key_uuid: uuid.UUID) -> dict[str, Any]:
  deleted = get_api_key_store().delete_api_key(user, key_uuid)
  if not deleted:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
  return {"deleted": True, "uuid": str(key_uuid)}


def authenticate_bearer_token(raw_token: str) -> Optional[dict[str, Any]]:
  return get_api_key_store().authenticate_api_key(raw_token)


def _row_to_record(row: Any) -> ApiKeyRecord:
  return ApiKeyRecord(
    key_uuid=row[0],
    user_identifier=row[1],
    user_data=dict(row[2]),
    key_hash=row[3],
    description=row[4],
    created_at=_normalize_datetime(row[5]) or datetime.now(timezone.utc),
    expires_at=_normalize_datetime(row[6]),
    last_used_at=_normalize_datetime(row[7]),
  )


def _user_identifier(user: dict[str, Any]) -> str:
  if user.get("id") is not None:
    return f"github:{user['id']}"
  for field_name in ("login", "email", "sub", "name"):
    value = user.get(field_name)
    if value:
      return f"{field_name}:{value}"
  raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authenticated user profile is missing a stable identifier")


def _normalize_datetime(value: Optional[datetime]) -> Optional[datetime]:
  if value is None:
    return None
  if value.tzinfo is None:
    return value.replace(tzinfo=timezone.utc)
  return value.astimezone(timezone.utc)


def _is_active(expires_at: Optional[datetime]) -> bool:
  return expires_at is None or expires_at > datetime.now(timezone.utc)


def _build_raw_token(key_uuid: uuid.UUID) -> str:
  return f"{API_KEY_PREFIX}_{key_uuid}.{secrets.token_urlsafe(32)}"


def _parse_raw_token(raw_token: str) -> tuple[uuid.UUID, str]:
  if not raw_token.startswith(f"{API_KEY_PREFIX}_"):
    raise ValueError("invalid api key prefix")
  token_body = raw_token[len(API_KEY_PREFIX) + 1 :]
  if "." not in token_body:
    raise ValueError("invalid api key format")
  key_uuid_text, secret = token_body.split(".", 1)
  if not key_uuid_text or not secret:
    raise ValueError("invalid api key format")
  return uuid.UUID(key_uuid_text), secret


def _extract_secret(raw_token: str) -> str:
  return _parse_raw_token(raw_token)[1]


def _pepper() -> str:
  return settings.api_key_pepper or settings.session_secret or os.getenv("SESSION_SECRET", "") or "freeapi-api-key-pepper"


def _hash_secret(secret: str) -> str:
  value = f"{_pepper()}:{secret}"
  if HAS_ARGON2 and PASSWORD_HASHER is not None:
    return PASSWORD_HASHER.hash(value)

  salt = secrets.token_hex(16)
  digest = hashlib.pbkdf2_hmac("sha256", value.encode("utf-8"), salt.encode("utf-8"), 210000).hex()
  return f"pbkdf2_sha256$210000${salt}${digest}"


def _verify_secret(hash_value: str, secret: str) -> bool:
  value = f"{_pepper()}:{secret}"

  if HAS_ARGON2 and PASSWORD_HASHER is not None:
    try:
      PASSWORD_HASHER.verify(hash_value, value)
    except (InvalidHash, VerificationError, VerifyMismatchError):
      return False
    return True

  try:
    algorithm, iterations_text, salt, digest = hash_value.split("$", 3)
  except ValueError:
    return False

  if algorithm != "pbkdf2_sha256":
    return False

  try:
    iterations = int(iterations_text)
  except ValueError:
    return False

  candidate = hashlib.pbkdf2_hmac("sha256", value.encode("utf-8"), salt.encode("utf-8"), iterations).hex()
  return hmac.compare_digest(candidate, digest)
