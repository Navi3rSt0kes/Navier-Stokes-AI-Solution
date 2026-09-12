from __future__ import annotations

from ..models import AgentRequest, ProductRequirement, ShoppingPlan


class RuleBasedPlanner:
    """Predictable local planner used by the demo and test suite."""

    async def plan(self, request: AgentRequest) -> ShoppingPlan:
        text = request.message.lower()
        if any(word in text for word in ("torta", "pastel", "cake")):
            requirements = [
                ProductRequirement(query="flour"),
                ProductRequirement(query="sugar"),
                ProductRequirement(query="eggs"),
                ProductRequirement(query="milk"),
                ProductRequirement(query="cocoa chocolate"),
            ]
            return ShoppingPlan(summary="Core ingredients for a chocolate cake.", requirements=requirements)
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
            summary="I will look for the requested product or concept.",
            requirements=[ProductRequirement(query=request.message)],
        )
