from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


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
