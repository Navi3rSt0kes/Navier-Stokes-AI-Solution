from __future__ import annotations

from ..models import CartItem, CartSnapshot, Product


class MockCatalogGateway:
    """Local data solely for demos and tests; production data remains external."""

    def __init__(self, products: list[Product] | None = None) -> None:
        self.products = products or demo_products()

    async def search_catalog(
        self, store_id: str, query: str, filters: dict[str, str], limit: int = 10
    ) -> list[Product]:
        terms = set(query.lower().replace("-", " ").split())
        matches: list[tuple[int, Product]] = []
        for product in self.products:
            if product.store_id != store_id or product.stock <= 0:
                continue
            haystack = " ".join(
                [product.name, product.category, product.description, *product.tags]
            ).lower()
            score = len(terms & set(haystack.replace("-", " ").split()))
            if score:
                matches.append((score, product))
        return [
            product
            for _, product in sorted(matches, key=lambda result: (-result[0], result[1].price_minor))[:limit]
        ]


class MockCartGateway:
    def __init__(self) -> None:
        self._carts: dict[str, CartSnapshot] = {}
        self._idempotent_results: dict[str, CartSnapshot] = {}

    async def get_cart(self, cart_id: str) -> CartSnapshot:
        return self._carts.get(cart_id, CartSnapshot(cart_id=cart_id, currency="COP"))

    async def add_items_to_cart(
        self, cart_id: str, items: list[CartItem], idempotency_key: str
    ) -> CartSnapshot:
        if idempotency_key in self._idempotent_results:
            return self._idempotent_results[idempotency_key]
        current = await self.get_cart(cart_id)
        merged: dict[str, CartItem] = {item.product_id: item.model_copy() for item in current.items}
        for item in items:
            previous = merged.get(item.product_id)
            if previous:
                previous.quantity += item.quantity
            else:
                merged[item.product_id] = item.model_copy()
        values = list(merged.values())
        snapshot = CartSnapshot(
            cart_id=cart_id,
            items=values,
            total_minor=sum(item.line_total_minor for item in values),
            currency=current.currency,
        )
        self._carts[cart_id] = snapshot
        self._idempotent_results[idempotency_key] = snapshot
        return snapshot


def demo_products() -> list[Product]:
    raw = [
        ("cake-flour", "Harina de trigo 1 kg", "reposteria", 4_000, 20, ["harina", "torta", "pastel"]),
        ("cake-sugar", "Azúcar blanca 1 kg", "reposteria", 3_000, 30, ["azucar", "torta", "pastel"]),
        ("cake-eggs", "Huevos x 12", "reposteria", 8_000, 15, ["huevos", "torta", "pastel"]),
        ("cake-milk", "Leche entera 1 L", "reposteria", 4_500, 20, ["leche", "torta", "pastel"]),
        ("cake-cocoa", "Cocoa en polvo 250 g", "reposteria", 7_000, 10, ["cocoa", "chocolate", "torta"]),
        ("paint-acrylic", "Pintura acrílica set básico", "arte", 14_000, 8, ["pintura", "acrilico", "cuadro"]),
        ("paint-brush", "Pinceles para pintura x 3", "arte", 6_000, 12, ["pincel", "pintura", "cuadro"]),
        ("paint-canvas", "Lienzo 30 x 40 cm", "arte", 10_000, 12, ["lienzo", "canvas", "cuadro"]),
        ("tool-hammer", "Martillo de acero", "herramientas", 18_000, 8, ["martillo", "construccion", "casa"]),
        ("tool-nails", "Clavos 1 pulgada x 100", "herramientas", 5_000, 20, ["clavos", "construccion", "casa"]),
        ("home-detergent", "Detergente líquido 1 L", "hogar", 12_000, 20, ["limpieza", "hogar"]),
    ]
    return [
        Product(
            id=identifier,
            store_id="demo-store",
            sku=f"SKU-{identifier.upper()}",
            name=name,
            category=category,
            description=name,
            tags=tags,
            price_minor=price,
            stock=stock,
        )
        for identifier, name, category, price, stock, tags in raw
    ]
