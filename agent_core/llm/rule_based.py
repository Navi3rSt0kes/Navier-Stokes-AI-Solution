from __future__ import annotations

from ..models import AgentRequest, ProductRequirement, ShoppingPlan


class RuleBasedPlanner:
    """Predictable local planner used by the demo and test suite."""

    async def plan(self, request: AgentRequest) -> ShoppingPlan:
        text = request.message.lower()
        if any(word in text for word in ("torta", "pastel", "cake")):
            requirements = [
                ProductRequirement(query="harina"),
                ProductRequirement(query="azucar"),
                ProductRequirement(query="huevos"),
                ProductRequirement(query="leche"),
                ProductRequirement(query="cocoa chocolate"),
            ]
            return ShoppingPlan(summary="Ingredientes base para una torta de chocolate.", requirements=requirements)
        if any(word in text for word in ("pintar", "cuadro", "lienzo")):
            return ShoppingPlan(
                summary="Materiales básicos para pintar un cuadro.",
                requirements=[
                    ProductRequirement(query="pintura acrilico"),
                    ProductRequirement(query="pincel"),
                    ProductRequirement(query="lienzo"),
                ],
            )
        if any(word in text for word in ("construir", "casa", "reparar")):
            return ShoppingPlan(
                summary="Herramientas básicas disponibles para una tarea de construcción.",
                requirements=[ProductRequirement(query="martillo"), ProductRequirement(query="clavos")],
            )
        # The deterministic executor will report a missing product rather than guessing.
        return ShoppingPlan(
            summary="Buscaré el producto o concepto solicitado.",
            requirements=[ProductRequirement(query=request.message)],
        )
