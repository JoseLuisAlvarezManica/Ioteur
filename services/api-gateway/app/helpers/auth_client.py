import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class AuthClient:
    def __init__(self, session: httpx.AsyncClient):
        self.session = session

    async def post(self, endpoint: str, data: dict, headers: dict | None = None):
        logger.info("AuthClient POST %s", endpoint)
        response = await self.session.post(endpoint, json=data, headers=headers or {})
        return response.status_code, response.json()

    async def put(self, endpoint: str, data: dict, headers: dict | None = None):
        logger.info("AuthClient PUT %s", endpoint)
        response = await self.session.put(endpoint, json=data, headers=headers or {})
        return response.status_code, response.json()

    async def delete(self, endpoint: str, headers: dict | None = None):
        logger.info("AuthClient DELETE %s", endpoint)
        response = await self.session.delete(endpoint, headers=headers or {})
        return response.status_code, response.json()

    async def get(self, endpoint: str, headers: dict | None = None):
        logger.info("AuthClient GET %s", endpoint)
        response = await self.session.get(endpoint, headers=headers or {})
        return response.status_code, response.json()

    async def patch(self, endpoint: str, data: dict, headers: dict | None = None):
        logger.info("AuthClient PATCH %s", endpoint)
        response = await self.session.patch(endpoint, json=data, headers=headers or {})
        return response.status_code, response.json()


async def get_auth_client():
    async with httpx.AsyncClient(
        base_url=settings.AUTH_SERVICE_URL,
        timeout=10.0,
    ) as session:
        yield AuthClient(session)
