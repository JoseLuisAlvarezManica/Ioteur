import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


async def http_get(
    base_url: str, endpoint: str, params: dict | None = None
) -> tuple[int, Any]:
    async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
        response = await client.get(endpoint, params=params)
    try:
        return response.status_code, response.json()
    except Exception:
        return response.status_code, {"detail": response.text}
