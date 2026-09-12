from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from ..config import Settings
from ..models import CartItem, CartSnapshot, Product


class ExternalServiceError(RuntimeError):
    """An external business API could not fulfill a tool request."""


class _HttpGateway:
    def __init__(self, settings: Settings, base_url: str) -> None:
        self.settings = settings
        self.base_url = base_url.rstrip("/")

    @property
    def headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.settings.service_api_token:
            headers["Authorization"] = f"Bearer {self.settings.service_api_token}"
        return headers

    async def _request(
        self, method: str, path: str, *, json: dict[str, Any] | None = None, headers: dict[str, str] | None = None
    ) -> Any:
        url = f"{self.base_url}{path}"
        merged_headers = self.headers | (headers or {})
        last_error: Exception | None = None
        for attempt in range(self.settings.http_max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.settings.http_timeout_seconds) as client:
                    response = await client.request(method, url, json=json, headers=merged_headers)
                response.raise_for_status()
                return response.json()
            except (httpx.HTTPError, ValueError) as error:
                last_error = error
                if attempt < self.settings.http_max_retries:
                    await asyncio.sleep(0.1 * (2**attempt))
        raise ExternalServiceError(f"External request {method} {path} failed") from last_error


class HttpCatalogGateway(_HttpGateway):
    def __init__(self, settings: Settings) -> None:
        if not settings.catalog_api_base_url:
            raise ValueError("CATALOG_API_BASE_URL is required for HttpCatalogGateway")
        super().__init__(settings, settings.catalog_api_base_url)

    async def search_catalog(
        self, store_id: str, query: str, filters: dict[str, str], limit: int = 10
    ) -> list[Product]:
        payload = {"store_id": store_id, "query": query, "filters": filters, "limit": limit}
        data = await self._request("POST", self.settings.catalog_search_path, json=payload)
        rows = data.get("products", data) if isinstance(data, dict) else data
        return [Product.model_validate(row) for row in rows]


class HttpCartGateway(_HttpGateway):
    def __init__(self, settings: Settings) -> None:
        if not settings.cart_api_base_url:
            raise ValueError("CART_API_BASE_URL is required for HttpCartGateway")
        super().__init__(settings, settings.cart_api_base_url)

    async def get_cart(self, cart_id: str) -> CartSnapshot:
        path = self.settings.cart_get_path.format(cart_id=cart_id)
        return CartSnapshot.model_validate(await self._request("GET", path))

    async def add_items_to_cart(
        self, cart_id: str, items: list[CartItem], idempotency_key: str
    ) -> CartSnapshot:
        path = self.settings.cart_add_items_path.format(cart_id=cart_id)
        payload = {"items": [item.model_dump() for item in items]}
        headers = {"Idempotency-Key": idempotency_key}
        return CartSnapshot.model_validate(await self._request("POST", path, json=payload, headers=headers))
