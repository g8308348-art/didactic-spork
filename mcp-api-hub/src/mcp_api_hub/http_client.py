from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .config import settings
from .logging import get_logger

logger = get_logger(__name__)


class ServiceAuth:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def headers(self) -> Dict[str, str]:
        if self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}
        return {}


def _timeout_for(service_timeout: Optional[int]) -> httpx.Timeout:
    seconds = service_timeout or settings.DEFAULT_TIMEOUT
    return httpx.Timeout(seconds)


@retry(
    reraise=True,
    stop=stop_after_attempt(settings.RETRY_MAX),
    wait=wait_exponential(multiplier=0.25, min=0.5, max=5),
    retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout)),
)
async def request_json(
    method: str,
    url: str,
    *,
    json_body: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout_seconds: Optional[int] = None,
) -> Tuple[Dict[str, Any], int, float]:
    """Perform an HTTP request and return (json_or_error, status_code, elapsed_ms).

    If the response body is not JSON, returns a normalized error payload.
    """
    timeout = _timeout_for(timeout_seconds)
    merged_headers = {"Content-Type": "application/json"}
    if headers:
        merged_headers.update(headers)

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        resp = await client.request(method.upper(), url, json=json_body, headers=merged_headers)
        elapsed_ms = resp.elapsed.total_seconds() * 1000.0
        try:
            data = resp.json()
        except json.JSONDecodeError:
            data = {
                "status": "error",
                "message": "Non-JSON response",
                "raw": resp.text[:2000],
            }
        return data, resp.status_code, elapsed_ms
