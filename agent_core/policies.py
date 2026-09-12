from __future__ import annotations

from .models import AgentRequest


class CartWritePolicy:
    """Keeps authorization in the caller's hands, not in the language model's."""

    def __init__(self, mode: str = "authorized_only") -> None:
        if mode not in {"authorized_only", "never"}:
            raise ValueError("CART_WRITE_POLICY must be 'authorized_only' or 'never'")
        self.mode = mode

    def permits(self, request: AgentRequest) -> bool:
        return self.mode == "authorized_only" and request.cart_write_authorized
