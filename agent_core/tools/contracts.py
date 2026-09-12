from __future__ import annotations

from typing import Protocol

from ..models import CartItem, CartSnapshot, Product


class CatalogGateway(Protocol):
    async def search_catalog(
        self, store_id: str, query: str, filters: dict[str, str], limit: int = 10
    ) -> list[Product]: ...


class CartGateway(Protocol):
    async def get_cart(self, cart_id: str) -> CartSnapshot: ...

    async def add_items_to_cart(
        self, cart_id: str, items: list[CartItem], idempotency_key: str
    ) -> CartSnapshot: ...
