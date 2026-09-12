# Arquitectura

`shopping-agent-core` es una biblioteca de orquestación, no un backend de comercio.
Su único trabajo es transformar una petición humana en consultas y acciones contra
servicios que pertenecen a otros repositorios.

```text
Aplicación o backend llamador
        │ AgentRequest
        ▼
    AgentService
        │
        ├── Planificador (reglas locales u OpenAI)
        │       └── requisitos genéricos: "huevos", "lienzo", "martillo"
        │
        └── Ejecutor determinista
                ├── CatalogGateway.search_catalog(...) ──► API de catálogo ajena
                ├── CartGateway.get_cart(...) ───────────► API de carrito ajena
                └── CartGateway.add_items_to_cart(...) ─► API de carrito ajena
```

## Responsabilidades

El planificador solo propone conceptos y cantidades. Puede ser el proveedor local
para desarrollo o `OpenAIPlanner` en producción. No recibe la autoridad de escribir
en servicios externos y no establece precios ni disponibilidad.

El ejecutor valida todos los candidatos que devuelve el catálogo: moneda, stock,
precio y presupuesto. Solo convierte productos retornados por `CatalogGateway` en
artículos del carrito. El permiso `cart_write_authorized` se verifica antes de la
única operación con efecto lateral.

## Integración

Los protocolos `CatalogGateway` y `CartGateway` son los puertos de integración.
`HttpCatalogGateway` y `HttpCartGateway` son adaptadores HTTP configurables. Si las
APIs existentes usan otra forma de autenticación o JSON, se modifica únicamente el
adaptador correspondiente; el orquestador y los modelos del agente no cambian.

Cada escritura usa una clave de idempotencia derivada del contexto de la petición.
Los reintentos se aplican solo a solicitudes HTTP fallidas. Los adaptadores reales
siguen siendo responsables de aplicar sus propias reglas de autorización y de volver
a validar stock y precio de forma atómica.

## Límites deliberados

- No se persisten conversaciones, productos ni carritos aquí.
- No se expone un endpoint web: el backend dueño de la sesión importa `AgentService`
  o lo ejecuta desde un worker.
- No se devuelve razonamiento interno del modelo; solo una explicación y una traza de
  acciones de negocio apta para el usuario o el backend llamador.
