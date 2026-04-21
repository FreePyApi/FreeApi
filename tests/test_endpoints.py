import time

import pytest
from fastapi.testclient import TestClient

import src.config.api_keys as api_keys_module
from src.main import app
from src.config.security import serialize_auth_payload


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_api_key_store():
  api_keys_module._STORE = api_keys_module.MemoryApiKeyStore()
  yield
  api_keys_module._STORE = None


def test_gateway_redirects_unversioned_paths():
  response = client.get("/status", follow_redirects=False)

  assert response.status_code == 307
  assert response.headers["location"] == "/v1.0.0/status"


def test_versioned_status_endpoint_returns_ready_payload():
  response = client.get("/v1.0.0/status")

  assert response.status_code == 200
  body = response.json()
  assert body["status"] == "running"
  assert body["version"] == "1.0.0"


def test_text_count_returns_scalars():
  response = client.post("/v1.0.0/text/count", json="Hello world. Another sentence.")

  assert response.status_code == 200
  body = response.json()
  assert body["words"] == 4
  assert body["characters"] > 0
  assert body["sentences"] >= 2


def test_api_key_lifecycle_and_bearer_auth():
  user = {"id": 123456, "login": "tester", "name": "Tester"}
  auth_cookie = serialize_auth_payload({"user": user, "expires_at": int(time.time()) + 3600})

  with TestClient(app) as authed_client:
    authed_client.cookies.set("freeapi_auth", auth_cookie)

    create_response = authed_client.post("/v1.0.0/auth/api-keys", json={"description": "CI key"})
    assert create_response.status_code == 200
    create_body = create_response.json()
    assert create_body["api_key"].startswith("fpk_")
    assert create_body["key"]["uuid"]

    list_response = authed_client.get("/v1.0.0/auth/api-keys")
    assert list_response.status_code == 200
    list_body = list_response.json()
    assert len(list_body["keys"]) == 1
    assert "api_key" not in list_body["keys"][0]

    bearer_response = authed_client.get(
      "/v1.0.0/auth/me",
      headers={"Authorization": f"Bearer {create_body['api_key']}"},
    )
    assert bearer_response.status_code == 200
    bearer_body = bearer_response.json()
    assert bearer_body["authenticated"] is True
    assert bearer_body["user"]["login"] == "tester"

    delete_response = authed_client.delete(f"/v1.0.0/auth/api-keys/{create_body['key']['uuid']}")
    assert delete_response.status_code == 200
    delete_body = delete_response.json()
    assert delete_body["deleted"] is True

    empty_response = authed_client.get("/v1.0.0/auth/api-keys")
    assert empty_response.status_code == 200
    assert empty_response.json()["keys"] == []
