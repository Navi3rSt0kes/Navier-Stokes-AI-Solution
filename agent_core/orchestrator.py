from __future__ import annotations

import uuid
from typing import Protocol

from .models import (
    AgentRequest,
    AgentResponse,
    AgentStatus,
    CartAction,
    CartItem,
    ProductRequirement,
    RecommendedItem,
    ShoppingPlan,
)
from .policies import CartWritePolicy
from .tools.contracts import CartGateway, CatalogGateway


class Planner(Protocol):
    async def plan(self, request: AgentRequest) -> ShoppingPlan: ...


class ShoppingOrchestrator:
    """Executes a bounded plan with only catalogue and cart permissions."""

    def __init__(
        self,
        planner: Planner,
        catalog: CatalogGateway,
        cart: CartGateway,
        policy: CartWritePolicy,
        max_tool_rounds: int = 12,
    ) -> None:
        self.planner = planner
        self.catalog = catalog
        self.cart = cart
        self.policy = policy
        self.max_tool_rounds = max_tool_rounds

    async def run(self, request: AgentRequest) -> AgentResponse:
        try:
            current_cart = await self.cart.get_cart(request.cart_id)
            plan = await self.planner.plan(request)
            selected, missing = await self._resolve_plan(request, plan)
        except Exception as error:  # External errors become a safe result for the caller.
            return AgentResponse(
                message="No pude consultar los servicios necesarios en este momento.",
                status=AgentStatus.FAILED,
                currency=request.currency,
                warnings=[str(error)],
            )

        estimated_total = sum(item.line_total_minor for item in selected)
        projected_total = current_cart.total_minor + estimated_total
        if missing:
            return AgentResponse(
                message="Encontré una propuesta parcial, pero faltan productos necesarios.",
                status=AgentStatus.MISSING_PRODUCTS,
                recommended_items=selected,
                cart_snapshot=current_cart,
                estimated_total=estimated_total,
                currency=request.currency,
                missing_requirements=missing,
                warnings=["No se modificó el carrito."],
                metadata={"plan_summary": plan.summary},
            )
        if request.budget_minor is not None and projected_total > request.budget_minor:
            return AgentResponse(
                message="Los productos disponibles exceden el presupuesto indicado.",
                status=AgentStatus.BUDGET_EXCEEDED,
                recommended_items=selected,
                cart_snapshot=current_cart,
                estimated_total=estimated_total,
                currency=request.currency,
                warnings=[f"Total proyectado: {projected_total} {request.currency}.", "No se modificó el carrito."],
                metadata={"plan_summary": plan.summary},
            )
        if not self.policy.permits(request):
            return AgentResponse(
                message="Preparé una propuesta. Confirma la autorización para agregarla al carrito.",
                status=AgentStatus.NEEDS_CONFIRMATION,
                recommended_items=selected,
                cart_snapshot=current_cart,
                estimated_total=estimated_total,
                currency=request.currency,
                warnings=["El agente no tiene autorización para escribir en el carrito."],
                metadata={"plan_summary": plan.summary},
            )

        cart_items = [
            CartItem(
                product_id=item.product.id,
                quantity=item.quantity,
                unit_price_minor=item.product.price_minor,
                name=item.product.name,
            )
            for item in selected
        ]
        try:
            snapshot = await self.cart.add_items_to_cart(
                request.cart_id, cart_items, self._idempotency_key(request)
            )
        except Exception as error:
            return AgentResponse(
                message="La propuesta está lista, pero no fue posible actualizar el carrito.",
                status=AgentStatus.FAILED,
                recommended_items=selected,
                cart_snapshot=current_cart,
                estimated_total=estimated_total,
                currency=request.currency,
                warnings=[str(error)],
            )
        return AgentResponse(
            message="Agregué los productos disponibles al carrito.",
            status=AgentStatus.COMPLETED,
            recommended_items=selected,
            cart_actions=[
                CartAction(action="add_items_to_cart", product_id=item.product.id, quantity=item.quantity, result="added")
                for item in selected
            ],
            cart_snapshot=snapshot,
            estimated_total=estimated_total,
            currency=request.currency,
            metadata={"plan_summary": plan.summary},
        )

    async def _resolve_plan(
        self, request: AgentRequest, plan: ShoppingPlan
    ) -> tuple[list[RecommendedItem], list[str]]:
        selected: list[RecommendedItem] = []
        missing: list[str] = []
        for round_number, requirement in enumerate(plan.requirements, start=1):
            if round_number > self.max_tool_rounds:
                raise RuntimeError("Tool round limit reached")
            candidates = await self.catalog.search_catalog(
                request.store_id, requirement.query, requirement.filters, limit=10
            )
            product = self._select_candidate(candidates, requirement, request.currency)
            if product is None:
                if requirement.required:
                    missing.append(requirement.query)
                continue
            selected.append(
                RecommendedItem(
                    product=product,
                    quantity=requirement.quantity,
                    line_total_minor=product.price_minor * requirement.quantity,
                    matched_requirement=requirement.query,
                )
            )
        return selected, missing

    @staticmethod
    def _select_candidate(candidates, requirement: ProductRequirement, currency: str):
        eligible = [
            product
            for product in candidates
            if product.currency == currency and product.stock >= requirement.quantity
        ]
        # The catalogue gateway owns relevance ranking. Preserve its first valid match
        # instead of allowing a cheaper but less relevant item to win here.
        return eligible[0] if eligible else None

    @staticmethod
    def _idempotency_key(request: AgentRequest) -> str:
        seed = ":".join(
            [request.user_id, request.store_id, request.cart_id, request.conversation_id or "", request.message]
        )
        return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))
