from __future__ import annotations

from .config import Settings
from .llm import OpenAIPlanner, RuleBasedPlanner
from .models import AgentRequest, AgentResponse
from .orchestrator import ShoppingOrchestrator
from .policies import CartWritePolicy
from .tools.contracts import CartGateway, CatalogGateway
from .tools.http import HttpCartGateway, HttpCatalogGateway
from .tools.mock import MockCartGateway, MockCatalogGateway


class AgentService:
    """Public facade intended to be imported by another backend or worker."""

    def __init__(self, orchestrator: ShoppingOrchestrator) -> None:
        self._orchestrator = orchestrator

    async def run(self, request: AgentRequest) -> AgentResponse:
        return await self._orchestrator.run(request)

    @classmethod
    def create(
        cls,
        *,
        settings: Settings | None = None,
        catalog: CatalogGateway | None = None,
        cart: CartGateway | None = None,
    ) -> "AgentService":
        settings = settings or Settings.from_env()
        if settings.planner == "openai":
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required when AGENT_PLANNER=openai")
            planner = OpenAIPlanner(settings.openai_api_key, settings.openai_model)
        elif settings.planner == "mock":
            planner = RuleBasedPlanner()
        else:
            raise ValueError("AGENT_PLANNER must be 'mock' or 'openai'")
        catalog = catalog or (
            HttpCatalogGateway(settings) if settings.catalog_api_base_url else MockCatalogGateway()
        )
        cart = cart or (HttpCartGateway(settings) if settings.cart_api_base_url else MockCartGateway())
        return cls(ShoppingOrchestrator(planner, catalog, cart, CartWritePolicy(settings.cart_write_policy)))
