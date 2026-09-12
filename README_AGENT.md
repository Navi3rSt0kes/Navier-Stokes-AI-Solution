# Shopping Agent Core

Biblioteca Python para un agente de compras que entiende solicitudes en lenguaje
natural y opera contra APIs de catálogo y carrito que viven en otros repositorios.
No crea un e-commerce, no guarda inventario y no implementa checkout.

## Qué hace

1. Un planificador convierte una solicitud como “quiero una torta de chocolate” en
   requisitos genéricos.
2. El ejecutor consulta el catálogo externo para cada requisito.
3. Solo el ejecutor valida producto, moneda, stock, precio y presupuesto.
4. Si el llamador autoriza la escritura, el ejecutor llama al API de carrito con una
   clave de idempotencia; en caso contrario devuelve una propuesta.

El modelo nunca decide precios, stock ni IDs. Tampoco recibe permiso de red directo:
las únicas acciones disponibles son los adaptadores `CatalogGateway` y `CartGateway`.

## Instalación y demostración local

Requiere Python 3.11 o superior.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m agent_core.demo
python -m pytest
```

El modo predeterminado usa un catálogo y carrito simulados. No requiere clave ni
conexión a otros proyectos.

## Uso desde otro repositorio

Instala este proyecto como dependencia y llama al agente desde el backend que ya
gestiona las peticiones del cliente:

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

Con `cart_write_authorized=False`, el resultado tiene estado `needs_confirmation` y
no llama al carrito. Tras confirmar en tu aplicación, reenvía la solicitud con
`cart_write_authorized=True`.

## Conectar servicios reales

Copia `.env.example` a `.env` y configura las URLs de las APIs que ya existen:

```dotenv
AGENT_PLANNER=openai
OPENAI_API_KEY=tu_clave
OPENAI_MODEL=gpt-4o-mini
CART_WRITE_POLICY=authorized_only

CATALOG_API_BASE_URL=https://catalogo.ejemplo.com
CATALOG_SEARCH_PATH=/products/search
CART_API_BASE_URL=https://carrito.ejemplo.com
CART_GET_PATH=/carts/{cart_id}
CART_ADD_ITEMS_PATH=/carts/{cart_id}/items
SERVICE_API_TOKEN=token-del-servicio
```

Los adaptadores HTTP esperan estos contratos neutrales:

```text
POST CATALOG_SEARCH_PATH
{ "store_id", "query", "filters", "limit" }
→ { "products": [Product] }  o  [Product]

GET CART_GET_PATH
→ CartSnapshot

POST CART_ADD_ITEMS_PATH, cabecera Idempotency-Key
{ "items": [CartItem] }
→ CartSnapshot
```

Los tipos `Product`, `CartItem` y `CartSnapshot` están en `agent_core.models`. Si una
API externa tiene una forma diferente, adapta el mapeo en `agent_core/tools/http.py`
o implementa los protocolos de `agent_core/tools/contracts.py`; no cambies la lógica
del orquestador.

## Planificadores

- `AGENT_PLANNER=mock`: reglas locales para desarrollo y pruebas.
- `AGENT_PLANNER=openai`: `OpenAIPlanner` usa Responses API y function calling para
  producir un plan estructurado. El resultado contiene conceptos, nunca productos
  inventados; el ejecutor sigue consultando los servicios externos.

## Estados de respuesta

| Estado | Significado |
| --- | --- |
| `completed` | Se agregaron artículos autorizados al carrito. |
| `needs_confirmation` | Hay propuesta, pero falta autorización de escritura. |
| `missing_products` | Falta al menos un requisito indispensable. |
| `budget_exceeded` | El total proyectado supera el presupuesto. |
| `failed` | Un planificador o API externa no estuvo disponible. |

Consulta [ARCHITECTURE.md](ARCHITECTURE.md) para las responsabilidades y límites de
cada componente.
