from typing import Optional, Dict, Any

from pydantic import BaseModel, Field
from pydantic import StringConstraints
from typing_extensions import Annotated

from ..config import settings
from ..http_client import request_json
from ..logging import get_logger

log = get_logger(__name__)


class BpmRequest(BaseModel):
    transactionId: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=3, max_length=50)
    ]
    marketType: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1)
    ]
    timeoutSeconds: Optional[int] = Field(
        default=None, description="Override timeout for this call in seconds"
    )


def _bpm_base_url() -> str:
    return (settings.BPM_URL or "http://localhost:8088").rstrip("/")


def register(mcp) -> None:
    @mcp.tool()
    async def bpm_search_tool(payload: dict) -> dict:
        """Search BPM for a transaction.
        
        Calls the local Flask endpoint `/api/bpm` with JSON body {transactionId, marketType}.
        Returns backend JSON with added _clientMeta. Sets isError when HTTP>=400 or status=='error'.
        """
        # Validate and normalize input using Pydantic v2
        req = BpmRequest.model_validate(payload)

        url = f"{_bpm_base_url()}/api/bpm"
        body = {"transactionId": req.transactionId, "marketType": req.marketType}

        headers: Dict[str, str] = {}

        data, status, elapsed_ms = await request_json(
            "POST",
            url,
            json_body=body,
            headers=headers,
            timeout_seconds=req.timeoutSeconds,
        )

        # Normalize envelope
        is_error = status >= 400 or (isinstance(data, dict) and data.get("status") == "error")
        meta = {"endpoint": "/api/bpm", "httpStatus": status, "elapsedMs": round(elapsed_ms, 2)}

        if isinstance(data, dict):
            data.setdefault("_clientMeta", meta)
            data.setdefault("isError", is_error)
            return data
        else:  # pragma: no cover - defensive
            return {
                "status": "error" if is_error else "ok",
                "message": "Unexpected non-dict response from BPM endpoint",
                "raw": str(data)[:500],
                "_clientMeta": meta,
                "isError": True,
            }
