import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class CallClient:
    def __init__(self, session: httpx.AsyncClient):
        self.session = session

    async def post(self, endpoint: str, data: dict):
        logger.info("CallClient POST %s", endpoint)
        response = await self.session.post(endpoint, json=data)
        return response.status_code, response.json()

    async def put(self, endpoint: str, data: dict):
        logger.info("CallClient PUT %s", endpoint)
        response = await self.session.put(endpoint, json=data)
        return response.status_code, response.json()

    async def get(self, endpoint: str, params: dict | None = None):
        logger.info("CallClient GET %s", endpoint)
        response = await self.session.get(endpoint, params=params)
        return response.status_code, response.json()

    async def delete(self, endpoint: str):
        logger.info("CallClient DELETE %s", endpoint)
        response = await self.session.delete(endpoint)
        return response.status_code, response.json()


async def get_call_client():
    async with httpx.AsyncClient(
        base_url=settings.CALL_SERVICE_URL,
        timeout=10.0,
    ) as session:
        yield CallClient(session)
