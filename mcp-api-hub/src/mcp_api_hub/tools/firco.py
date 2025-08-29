from __future__ import annotations

from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, constr

from ..config import settings
from ..http_client import request_json
from ..logging import get_logger

log = get_logger(__name__)


class FircoRequest(BaseModel):
    transaction: constr(strip_whitespace=True, min_length=1)
    action: constr(strip_whitespace=True, min_length=1)
    comment: constr(strip_whitespace=True) = ""
    transactionType: Optional[str] = Field(default="", description="Optional transaction type")
    performOnLatest: Optional[bool] = Field(default=False, description="If true, perform action on the latest")
    timeoutSeconds: Optional[int] = Field(
        default=None, description="Override timeout for this call in seconds"
    )


def _base_url() -> str:
    # Reuse BPM_URL default since both are served by the same Flask app by default
    return (settings.BPM_URL or "http://localhost:8088").rstrip("/")


def register(mcp) -> None:
    @mcp.tool()
    async def firco_process_tool(payload: FircoRequest) -> dict:
        """Execute a Firco automation via the Flask `/api` endpoint.
        
        Expects {transaction, action, comment, transactionType?, performOnLatest?} and forwards them.
        Returns backend JSON with `_clientMeta` and `isError` normalization.
        """
        url = f"{_base_url()}/api"
        body = {
            "transaction": payload.transaction,
            "action": payload.action,
            "comment": payload.comment,
            "transactionType": payload.transactionType or "",
            "performOnLatest": bool(payload.performOnLatest or False),
        }

        headers: Dict[str, str] = {}

        data, status, elapsed_ms = await request_json(
            "POST",
            url,
            json_body=body,
            headers=headers,
            timeout_seconds=payload.timeoutSeconds,
        )

        is_error = status >= 400 or (isinstance(data, dict) and data.get("success") is False) or (
            isinstance(data, dict) and data.get("status") == "error"
        )
        meta = {"endpoint": "/api", "httpStatus": status, "elapsedMs": round(elapsed_ms, 2)}

        if isinstance(data, dict):
            data.setdefault("_clientMeta", meta)
            data.setdefault("isError", is_error)
            return data
        else:  # pragma: no cover
            return {
                "status": "error" if is_error else "ok",
                "message": "Unexpected non-dict response from Firco endpoint",
                "raw": str(data)[:500],
                "_clientMeta": meta,
                "isError": True,
            }
