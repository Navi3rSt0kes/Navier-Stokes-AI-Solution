from __future__ import annotations

import asyncio

from .models import AgentRequest
from .service import AgentService


async def main() -> None:
    agent = AgentService.create()
    cases = [
        AgentRequest(
            message="Quiero hacer una torta de chocolate para 8 personas.",
            user_id="demo-user", store_id="demo-store", cart_id="demo-cart", budget_minor=30_000,
        ),
        AgentRequest(
            message="Quiero pintar un cuadro.", user_id="demo-user", store_id="demo-store", cart_id="art-cart",
            cart_write_authorized=True,
        ),
        AgentRequest(
            message="Quiero hacer una torta de chocolate.", user_id="demo-user", store_id="demo-store",
            cart_id="budget-cart", budget_minor=5_000,
        ),
    ]
    for request in cases:
        response = await agent.run(request)
        print(response.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
