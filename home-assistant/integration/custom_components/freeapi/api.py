from __future__ import annotations

from typing import Any

import aiohttp

from .const import CONF_ACCESS_TOKEN, CONF_API_KEY, CONF_API_VERSION, DEFAULT_API_VERSION


class FreeApiClient:
  def __init__(self, session: aiohttp.ClientSession, config: dict[str, Any]) -> None:
    self._session = session
    self._config = config

  @property
  def base_url(self) -> str:
    return (self._config.get("base_url") or "").rstrip("/")

  @property
  def api_version(self) -> str:
    version = str(self._config.get(CONF_API_VERSION) or DEFAULT_API_VERSION).strip()
    return version.lstrip("v")

  def _headers(self) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    access_token = self._config.get(CONF_ACCESS_TOKEN)
    api_key = self._config.get(CONF_API_KEY)
    if access_token:
      headers["Authorization"] = f"Bearer {access_token}"
    elif api_key:
      headers["Authorization"] = f"Bearer {api_key}"
    return headers

  async def _request(
    self,
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json_data: Any = None,
    timeout: int = 15,
  ) -> Any:
    if not self.base_url:
      raise ValueError("Missing base_url in FreeAPI configuration")
    versioned_path = path if path.startswith("/") else f"/{path}"
    url = f"{self.base_url}/v{self.api_version}{versioned_path}"
    async with self._session.request(
      method,
      url,
      headers=self._headers(),
      params=params,
      json=json_data,
      ssl=self._config.get("verify_ssl", True),
      timeout=aiohttp.ClientTimeout(total=timeout),
    ) as response:
      if response.status >= 400:
        text = await response.text()
        raise aiohttp.ClientResponseError(
          request_info=response.request_info,
          history=response.history,
          status=response.status,
          message=text,
          headers=response.headers,
        )
      if response.content_type == "application/json":
        return await response.json()
      return await response.text()

  async def get_status(self) -> dict[str, Any]:
    data = await self._request("GET", "/status")
    if isinstance(data, dict):
      return data
    return {"status": "unknown", "raw": str(data)}

  async def call_endpoint(
    self,
    endpoint: str,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    payload: Any = None,
  ) -> Any:
    return await self._request(method.upper(), endpoint, params=params, json_data=payload)
