import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List


@dataclass
class Product:
    sku: str
    name: str
    price: float
    quantity: int


class InventoryManager:
    def __init__(self, storage_path: str = "inventory_data.json") -> None:
        self.storage_path = Path(storage_path)
        self.products: Dict[str, Product] = {}
        self.sales_log: List[dict] = []
        self._load()

    def _load(self) -> None:
        if not self.storage_path.exists():
            return
        data = json.loads(self.storage_path.read_text(encoding="utf-8"))
        for item in data.get("products", []):
            prod = Product(**item)
            self.products[prod.sku] = prod
        self.sales_log = data.get("sales_log", [])

    def _save(self) -> None:
        payload = {
            "products": [asdict(p) for p in self.products.values()],
            "sales_log": self.sales_log,
        }
        self.storage_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def add_product(self, sku: str, name: str, price: float, quantity: int) -> Product:
        sku = sku.strip().upper()
        if sku in self.products:
            existing = self.products[sku]
            existing.quantity += quantity
            existing.price = price
            existing.name = name
        else:
            self.products[sku] = Product(sku=sku, name=name, price=price, quantity=quantity)
        self._save()
        return self.products[sku]

    def record_sale(self, sku: str, quantity: int) -> dict:
        sku = sku.strip().upper()
        if sku not in self.products:
            raise KeyError(f"Product '{sku}' not found.")
        product = self.products[sku]
        if quantity <= 0:
            raise ValueError("Sale quantity must be greater than zero.")
        if product.quantity < quantity:
            raise ValueError(f"Insufficient stock for {product.name} ({product.quantity} available).")

        product.quantity -= quantity
        sale_record = {
            "sku": sku,
            "name": product.name,
            "quantity": quantity,
            "unit_price": product.price,
            "total": round(product.price * quantity, 2),
        }
        self.sales_log.append(sale_record)
        self._save()
        return sale_record

    def total_units(self) -> int:
        return sum(p.quantity for p in self.products.values())

    def total_stock_value(self) -> float:
        return round(sum(p.price * p.quantity for p in self.products.values()), 2)

    def to_context_summary(self) -> str:
        if not self.products:
            return "Inventory is currently empty."
        lines = [
            f"- [{p.sku}] {p.name}: {p.quantity} in stock @ ${p.price:.2f} each"
            for p in self.products.values()
        ]
        lines.append(f"Total units: {self.total_units()} | Total stock value: ${self.total_stock_value():.2f}")
        lines.append(f"Total recorded sales: {len(self.sales_log)}")
        return "\n".join(lines)
