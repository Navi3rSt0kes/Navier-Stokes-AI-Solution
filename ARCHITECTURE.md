# Architecture

`shopping-agent-core` is an orchestration library, not a commerce backend. Its only job is to turn a human request
into queries and actions against services that belong to other repositories.

```text
Calling application or backend
        │ AgentRequest
        ▼
    AgentService
        │
        ├── Planner (local rules or OpenAI)
        │       └── generic requirements: "eggs", "canvas", "hammer"
        │
        └── Deterministic executor
                ├── CatalogGateway.search_catalog(...) ──► external catalogue API
                ├── CartGateway.get_cart(...) ───────────► external cart API
                └── CartGateway.add_items_to_cart(...) ─► external cart API
```

## Responsibilities

**The planner** only proposes concepts and quantities. It can be the local provider for development or
`OpenAIPlanner` in production. It is not granted authority to write to external services and does not set prices or
availability. Its output is capped at 12 requirements, each with a quantity between 1 and 50.

**The executor** validates every candidate returned by the catalogue: currency, stock, price, and budget. It converts
only products returned by `CatalogGateway` into cart items. The `cart_write_authorized` permission is checked before
the single side-effecting operation.

**`CartWritePolicy`** keeps authorization in the caller's hands rather than the language model's. In
`authorized_only` mode a write requires an explicit `cart_write_authorized=True` on the request; in `never` mode no
write is ever performed.

## Decision order

`ShoppingOrchestrator.run()` evaluates outcomes in a fixed order, and each terminal state returns immediately:

1. Read the cart snapshot and build the plan. Any failure here yields `failed`.
2. Resolve each requirement against the catalogue, keeping the gateway's first candidate whose currency matches the
   request and whose stock covers the quantity. Relevance ranking belongs to the gateway; the executor does not
   re-rank, so a cheaper but less relevant item cannot displace the catalogue's best match.
3. Any unmet required requirement → `missing_products`.
4. Current cart total plus the proposal above `budget_minor` → `budget_exceeded`.
5. Policy does not permit the write → `needs_confirmation`.
6. Otherwise perform the write → `completed`, or `failed` if the cart API rejects it.

States 3 to 5 always leave the cart untouched and say so in `warnings`.

## Integration

The `CatalogGateway` and `CartGateway` protocols are the integration ports. `HttpCatalogGateway` and
`HttpCartGateway` are configurable HTTP adapters. If the existing APIs use a different authentication scheme or JSON
shape, only the corresponding adapter changes; the orchestrator and the agent models stay the same.

When no base URL is configured, `AgentService.create()` falls back to the in-memory mock gateways, which is what makes
the demo and the test suite runnable offline.

Every write uses an idempotency key derived from the request context — a `uuid5` over user, store, cart, conversation,
and message — sent as the `Idempotency-Key` header. Retries apply only to failed HTTP requests. Real adapters remain
responsible for enforcing their own authorization rules and for re-validating stock and price atomically.

## Deliberate limits

- No conversations, products, or carts are persisted here.
- No web endpoint is exposed: the backend that owns the session imports `AgentService` or runs it from a worker.
- No internal model reasoning is returned; only a user-facing explanation and a trace of business actions suitable for
  the user or the calling backend.
