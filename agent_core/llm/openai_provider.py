from __future__ import annotations

import asyncio
import json
from typing import Any

from ..models import AgentRequest, ShoppingPlan
from ..prompts import PLANNER_INSTRUCTIONS


PLAN_TOOL: dict[str, Any] = {
    "type": "function",
    "name": "submit_shopping_plan",
    "description": "Submit generic product requirements for deterministic catalogue lookup.",
    "strict": True,
    "parameters": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "summary": {"type": "string"},
            "requirements": {
                "type": "array",
                "minItems": 1,
                "maxItems": 12,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "query": {"type": "string"},
                        "quantity": {"type": "integer", "minimum": 1, "maximum": 50},
                        "required": {"type": "boolean"},
                        "filters": {
                            "type": "object",
                            "additionalProperties": {"type": "string"},
                        },
                    },
                    "required": ["query", "quantity", "required", "filters"],
                },
            },
        },
        "required": ["summary", "requirements"],
    },
}


class OpenAIPlanner:
    """Model-backed planner. It emits requirements; it never receives inventory as truth."""

    def __init__(self, api_key: str, model: str) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model

    async def plan(self, request: AgentRequest) -> ShoppingPlan:
        user_input = {
            "message": request.message,
            "currency": request.currency,
            "budget_minor": request.budget_minor,
            "store_id": request.store_id,
        }
        response = await asyncio.to_thread(
            self.client.responses.create,
            model=self.model,
            instructions=PLANNER_INSTRUCTIONS,
            input=json.dumps(user_input, ensure_ascii=False),
            tools=[PLAN_TOOL],
            tool_choice={"type": "function", "name": "submit_shopping_plan"},
        )
        for item in response.output:
            if getattr(item, "type", None) == "function_call" and item.name == "submit_shopping_plan":
                return ShoppingPlan.model_validate(json.loads(item.arguments))
        raise RuntimeError("The planning model did not return a shopping plan")
