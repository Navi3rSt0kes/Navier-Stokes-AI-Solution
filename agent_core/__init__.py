"""A transport-independent shopping-agent integration layer."""

from .models import AgentRequest, AgentResponse
from .service import AgentService

__all__ = ["AgentRequest", "AgentResponse", "AgentService"]
