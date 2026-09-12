from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    planner: str = "mock"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    cart_write_policy: str = "authorized_only"
    http_timeout_seconds: float = 10.0
    http_max_retries: int = 2
    service_api_token: str | None = None
    catalog_api_base_url: str | None = None
    catalog_search_path: str = "/products/search"
    cart_api_base_url: str | None = None
    cart_get_path: str = "/carts/{cart_id}"
    cart_add_items_path: str = "/carts/{cart_id}/items"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            planner=os.getenv("AGENT_PLANNER", "mock"),
            openai_api_key=os.getenv("OPENAI_API_KEY") or None,
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            cart_write_policy=os.getenv("CART_WRITE_POLICY", "authorized_only"),
            http_timeout_seconds=float(os.getenv("HTTP_TIMEOUT_SECONDS", "10")),
            http_max_retries=int(os.getenv("HTTP_MAX_RETRIES", "2")),
            service_api_token=os.getenv("SERVICE_API_TOKEN") or None,
            catalog_api_base_url=os.getenv("CATALOG_API_BASE_URL") or None,
            catalog_search_path=os.getenv("CATALOG_SEARCH_PATH", "/products/search"),
            cart_api_base_url=os.getenv("CART_API_BASE_URL") or None,
            cart_get_path=os.getenv("CART_GET_PATH", "/carts/{cart_id}"),
            cart_add_items_path=os.getenv("CART_ADD_ITEMS_PATH", "/carts/{cart_id}/items"),
        )
