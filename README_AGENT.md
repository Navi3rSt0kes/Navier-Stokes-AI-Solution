# Shopping Agent Core — integration guide

Python library for a shopping agent that understands natural-language requests and operates against catalogue and
cart APIs owned by other repositories. It does not build an e-commerce site, does not store inventory, and does not
implement checkout.

For the project overview, tech stack, configuration reference, and status table, see [README.md](README.md). This
document focuses on **using the library from another codebase**.

## What it does

1. A planner turns a request such as "quiero una torta de chocolate" into generic requirements.
2. The executor queries the external catalogue for each requirement.
3. Only the executor validates product, currency, stock, price, and budget.
4. If the caller authorizes the write, the executor calls the cart API with an idempotency key; otherwise it returns
   a proposal.

The model never decides prices, stock, or IDs, and is never granted direct network access: the only available actions
are the `CatalogGateway` and `CartGateway` adapters.

## Local installation and demo

Requires Python 3.11 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m agent_core.demo
python -m pytest
```

The default mode uses a simulated catalogue and cart. It requires no API key and no connection to other projects.

## Using it from another repository

Install this project as a dependency and call the agent from the backend that already handles client requests:

```python
from agent_core import AgentRequest, AgentService

agent = AgentService.create()

result = await agent.run(AgentRequest(
    message="Quiero hacer una torta de chocolate para 8 personas",
    user_id="user-123",
    store_id="store-456",
    cart_id="cart-789",
    currency="COP",
    budget_minor=30_000,
    cart_write_authorized=False,
))

return result.model_dump()
```

With `cart_write_authorized=False` the result has status `needs_confirmation` and the cart API is not called. After
the user confirms in your application, resend the request with `cart_write_authorized=True`.

### Request fields

| Field | Type | Notes |
| --- | --- | --- |
| `message` | `str` | 1–2000 characters |
| `user_id` | `str` | 1–128 characters |
| `store_id` | `str` | 1–128 characters; forwarded to the catalogue search |
| `cart_id` | `str` | 1–128 characters; substituted into the cart paths |
| `currency` | `str` | Exactly 3 characters, default `COP`. Candidates whose currency differs are discarded |
| `budget_minor` | `int \| None` | Smallest currency unit; compared against the current cart total plus the proposal |
| `cart_write_authorized` | `bool` | Default `False`. Required for any write |
| `conversation_id` | `str \| None` | Up to 128 characters; part of the idempotency key |

### Injecting your own gateways

```python
service = AgentService.create(catalog=MyCatalogGateway(), cart=MyCartGateway())
```

Any object satisfying the protocols in `agent_core/tools/contracts.py` is accepted — this is the intended extension
point when an existing API does not match the default HTTP shapes.

## Connecting real services

Copy `.env.example` to `.env` and configure the URLs of the APIs that already exist:

```dotenv
AGENT_PLANNER=openai
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini
CART_WRITE_POLICY=authorized_only

CATALOG_API_BASE_URL=https://catalog.example.com
CATALOG_SEARCH_PATH=/products/search
CART_API_BASE_URL=https://cart.example.com
CART_GET_PATH=/carts/{cart_id}
CART_ADD_ITEMS_PATH=/carts/{cart_id}/items
SERVICE_API_TOKEN=service-token
```

The library reads these through `Settings.from_env()`; it does not parse `.env` files itself, so export the variables
or load the file with your own tooling.

The HTTP adapters expect these neutral contracts:

```text
POST CATALOG_SEARCH_PATH
{ "store_id", "query", "filters", "limit" }
→ { "products": [Product] }  or  [Product]

GET CART_GET_PATH
→ CartSnapshot

POST CART_ADD_ITEMS_PATH, header Idempotency-Key
{ "items": [CartItem] }
→ CartSnapshot
```

`Product`, `CartItem`, and `CartSnapshot` live in `agent_core.models`. If an external API has a different shape,
adapt the mapping in `agent_core/tools/http.py` or implement the protocols in `agent_core/tools/contracts.py`; do not
change the orchestrator logic.

Both adapters send `Accept: application/json` and `Content-Type: application/json`, add
`Authorization: Bearer <SERVICE_API_TOKEN>` when that token is set, and retry `HTTP_MAX_RETRIES` times with
exponential backoff before raising `ExternalServiceError`.

> The MarkECIA services do not currently expose these routes. `Navi3rSt0kes-WereHouse` uses `GET /buscar` and
> `POST /carrito/validar`; `NavierStokes-ApiGateway` uses `GET /api/products` and `PUT /api/cart/items`. Connecting
> either one requires a custom gateway or a mapping change in the HTTP adapter.

## Planners

- `AGENT_PLANNER=mock`: local rules for development and testing. Recognizes cake, painting, and construction
  keywords; anything else is forwarded as a single requirement so the executor reports it as missing rather than
  guessing.
- `AGENT_PLANNER=openai`: `OpenAIPlanner` uses the Responses API with strict function calling to produce a structured
  plan. The result contains concepts, never invented products; the executor still queries the external services.

## Response statuses

| Status | Meaning |
| --- | --- |
| `completed` | Authorized items were added to the cart. |
| `needs_confirmation` | A proposal exists, but write authorization is missing. |
| `missing_products` | At least one indispensable requirement is unmet. |
| `budget_exceeded` | The projected total exceeds the stated budget. |
| `failed` | A planner or an external API was unavailable. |

See [ARCHITECTURE.md](ARCHITECTURE.md) for the responsibilities and limits of each component.
