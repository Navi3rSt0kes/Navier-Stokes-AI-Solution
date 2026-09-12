from __future__ import annotations

import asyncio

from agent_core.models import AgentRequest, AgentStatus
from agent_core.service import AgentService
from agent_core.tools.mock import MockCatalogGateway, MockCartGateway, demo_products


def run(request: AgentRequest, service: AgentService | None = None):
    return asyncio.run((service or AgentService.create()).run(request))


def request_for(message: str, **extra) -> AgentRequest:
    return AgentRequest(
        message=message,
        user_id="test-user",
        store_id="demo-store",
        cart_id="test-cart",
        **extra,
    )


def test_cake_under_budget_is_a_proposal_without_write_authorization() -> None:
    response = run(request_for("Quiero una torta de chocolate", budget_minor=30_000))

    assert response.status == AgentStatus.NEEDS_CONFIRMATION
    assert response.estimated_total == 26_500
    assert len(response.recommended_items) == 5
    assert response.cart_actions == []


def test_authorized_request_updates_the_cart() -> None:
    cart = MockCartGateway()
    service = AgentService.create(cart=cart)
    response = run(request_for("Quiero pintar un cuadro", cart_write_authorized=True), service)

    assert response.status == AgentStatus.COMPLETED
    assert response.cart_snapshot is not None
    assert len(response.cart_snapshot.items) == 3
    assert all(action.result == "added" for action in response.cart_actions)


def test_unknown_need_does_not_invent_products() -> None:
    response = run(request_for("Necesito un reactor espacial"))

    assert response.status == AgentStatus.MISSING_PRODUCTS
    assert response.recommended_items == []
    assert response.missing_requirements


def test_budget_exceeded_does_not_modify_cart() -> None:
    response = run(request_for("Quiero una torta de chocolate", budget_minor=5_000, cart_write_authorized=True))

    assert response.status == AgentStatus.BUDGET_EXCEEDED
    assert response.cart_actions == []
    assert response.cart_snapshot is not None
    assert response.cart_snapshot.items == []


def test_insufficient_stock_is_reported_as_missing() -> None:
    products = [product.model_copy() for product in demo_products()]
    eggs = next(product for product in products if product.id == "cake-eggs")
    eggs.stock = 0
    service = AgentService.create(catalog=MockCatalogGateway(products))

    response = run(request_for("Quiero una torta de chocolate"), service)

    assert response.status == AgentStatus.MISSING_PRODUCTS
    assert "huevos" in response.missing_requirements


def test_selected_ids_always_come_from_catalogue() -> None:
    catalogue = MockCatalogGateway()
    response = run(request_for("Quiero pintar un cuadro"), AgentService.create(catalog=catalogue))
    valid_ids = {product.id for product in catalogue.products}

    assert {item.product.id for item in response.recommended_items}.issubset(valid_ids)
