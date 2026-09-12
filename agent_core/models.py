from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    COMPLETED = "completed"
    NEEDS_CONFIRMATION = "needs_confirmation"
    MISSING_PRODUCTS = "missing_products"
    BUDGET_EXCEEDED = "budget_exceeded"
    FAILED = "failed"


class Product(BaseModel):
    id: str
    store_id: str
    sku: str
    name: str
    category: str
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    unit: str = "unit"
    price_minor: int = Field(ge=0, description="Price in the smallest currency unit")
    currency: str = "COP"
    stock: int = Field(ge=0)


class CartItem(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)
    unit_price_minor: int = Field(ge=0)
    name: str | None = None

    @property
    def line_total_minor(self) -> int:
        return self.quantity * self.unit_price_minor


class CartSnapshot(BaseModel):
    cart_id: str
    items: list[CartItem] = Field(default_factory=list)
    total_minor: int = Field(default=0, ge=0)
    currency: str = "COP"


class ProductRequirement(BaseModel):
    """A product concept, not a catalogue identifier supplied by the model."""

    query: str = Field(min_length=1, max_length=120)
    quantity: int = Field(default=1, gt=0, le=50)
    required: bool = True
    filters: dict[str, str] = Field(default_factory=dict)


class ShoppingPlan(BaseModel):
    summary: str
    requirements: list[ProductRequirement] = Field(min_length=1, max_length=12)


class RecommendedItem(BaseModel):
    product: Product
    quantity: int = Field(gt=0)
    line_total_minor: int = Field(ge=0)
    matched_requirement: str


class CartAction(BaseModel):
    action: str
    product_id: str | None = None
    quantity: int | None = None
    result: str


class AgentRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2_000)
    user_id: str = Field(min_length=1, max_length=128)
    store_id: str = Field(min_length=1, max_length=128)
    cart_id: str = Field(min_length=1, max_length=128)
    currency: str = Field(default="COP", min_length=3, max_length=3)
    budget_minor: int | None = Field(default=None, ge=0)
    cart_write_authorized: bool = False
    conversation_id: str | None = Field(default=None, max_length=128)


class AgentResponse(BaseModel):
    message: str
    status: AgentStatus
    recommended_items: list[RecommendedItem] = Field(default_factory=list)
    cart_actions: list[CartAction] = Field(default_factory=list)
    cart_snapshot: CartSnapshot | None = None
    estimated_total: int = Field(default=0, ge=0)
    currency: str
    missing_requirements: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
