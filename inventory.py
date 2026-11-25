import json
import math
from datetime import datetime
from pathlib import Path

# Store inventory.json and activity_log.json beside this file.
DATA_FILE = Path(__file__).with_name("inventory.json")
ACTIVITY_FILE = Path(__file__).with_name("activity_log.json")



def load_activity_log():
    """Load previously recorded activities."""

    if not ACTIVITY_FILE.exists():
        return []

    try:
        with open(ACTIVITY_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError("Activity log must contain a list.")

        return data

    except (json.JSONDecodeError, OSError, ValueError) as error:
        raise RuntimeError(f"Could not load activity history: {error}") from error


def save_activity_log():
    """Save activity history to JSON."""

    temp_file = ACTIVITY_FILE.with_suffix(".tmp")

    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(activity_log, file, indent=4)

    temp_file.replace(ACTIVITY_FILE)


def record_activity(action, product, quantity, unit, balance_after):
    """Record one successful inventory transaction."""

    activity = {
        "date": datetime.now().astimezone().isoformat(timespec="seconds"),
        "action": action,
        "product": product,
        "quantity": quantity,
        "unit": unit,
        "balance_after": balance_after,
    }

    activity_log.append(activity)
    save_activity_log()


# Load previous activity when the application starts.
activity_log = load_activity_log()


def get_activity_history(limit=10, product=None, action=None):
    """Retrieve recent inventory transactions."""

    history = activity_log.copy()

    if product:
        product_filter = product.strip().lower()
        history = [
            item
            for item in history
            if item["product"].strip().lower() == product_filter
        ]

    if action:
        action_filter = action.strip().lower()
        history = [
            item for item in history if item["action"].strip().lower() == action_filter
        ]

    # Newest transactions first.
    history.reverse()

    return history[:limit]


def get_sales_summary():
    """Summarize recorded sales by product and date."""

    sales = [item for item in activity_log if item["action"].lower() == "sale"]

    if not sales:
        return "No sales have been recorded yet."

    product_totals = {}
    daily_totals = {}

    for item in sales:
        product = item["product"]
        quantity = item["quantity"]
        unit = item["unit"]

        # Accumulate total quantity sold for each product.
        if product not in product_totals:
            product_totals[product] = {
                "quantity": 0,
                "unit": unit,
            }

        product_totals[product]["quantity"] += quantity

        sale_date = datetime.fromisoformat(item["date"]).date()
        date_key = sale_date.isoformat()
        daily_key = (date_key, product)

        if daily_key not in daily_totals:
            daily_totals[daily_key] = {
                "transactions": 0,
                "quantity": 0,
                "unit": unit,
            }

        daily_totals[daily_key]["transactions"] += 1
        daily_totals[daily_key]["quantity"] += quantity

    report = ["SALES SUMMARY"]
    report.append(f"Total sales transactions: {len(sales)}")

    report.append("\nQUANTITY SOLD BY PRODUCT:")

    for product, details in sorted(product_totals.items()):
        report.append(f"- {product.title()}: {details['quantity']} {details['unit']}")

    report.append("\nDAILY SALES:")

    for (date_key, product), details in sorted(
        daily_totals.items(),
        reverse=True,
    ):
        formatted_date = datetime.strptime(date_key, "%Y-%m-%d").strftime("%d %B %Y")

        report.append(
            f"- {formatted_date} | {product.title()}: "
            f"{details['quantity']} {details['unit']} "
            f"({details['transactions']} transactions)"
        )

    return "\n".join(report)




def load_inventory():
    """Load inventory from JSON storage (empty on the very first run)."""

    if not DATA_FILE.exists():
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Inventory file must contain a dictionary.")

        return data

    except (json.JSONDecodeError, OSError, ValueError) as error:
        raise RuntimeError(f"Could not load inventory: {error}") from error


def save_inventory():
    """Save inventory to JSON storage."""

    temp_file = DATA_FILE.with_suffix(".tmp")

    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(inventory, file, indent=4)

    temp_file.replace(DATA_FILE)


# Load inventory when the application starts.
inventory = load_inventory()

# Create inventory.json on the first run.
if not DATA_FILE.exists():
    save_inventory()



def add_product(name, quantity, unit, reorder_level=5):
    """Add a new product to inventory."""

    if not isinstance(name, str):
        return "Product name must be text."

    name = name.strip().lower()

    if not name:
        return "Product name cannot be empty."

    if (
        isinstance(quantity, bool)
        or not isinstance(quantity, (int, float))
        or not math.isfinite(quantity)
        or quantity <= 0
    ):
        return "Quantity must be greater than zero."

    if (
        isinstance(reorder_level, bool)
        or not isinstance(reorder_level, (int, float))
        or not math.isfinite(reorder_level)
        or reorder_level < 0
    ):
        return "Invalid reorder level."

    if not isinstance(unit, str) or not unit.strip():
        return "Unit cannot be empty."

    if name in inventory:
        return f"{name} already exists in inventory."

    inventory[name] = {
        "quantity": quantity,
        "unit": unit.strip(),
        "reorder_level": reorder_level,
    }

    save_inventory()

    record_activity(
        "new_product",
        name,
        quantity,
        unit.strip(),
        inventory[name]["quantity"],
    )

    return f"Added {quantity} {unit.strip()} of {name}."


def record_sale(name, quantity):
    """Record a sale and reduce available stock."""

    if not isinstance(name, str):
        return "Product name must be text."

    name = name.strip().lower()

    if name not in inventory:
        return f"{name} is not in inventory."

    if (
        isinstance(quantity, bool)
        or not isinstance(quantity, (int, float))
        or not math.isfinite(quantity)
        or quantity <= 0
    ):
        return "Sale quantity must be greater than zero."

    if quantity > inventory[name]["quantity"]:
        return "Not enough stock available."

    inventory[name]["quantity"] -= quantity

    save_inventory()

    record_activity(
        "sale",
        name,
        quantity,
        inventory[name]["unit"],
        inventory[name]["quantity"],
    )

    remaining = inventory[name]["quantity"]
    unit_name = inventory[name]["unit"]

    return (
        f"Sold {quantity} {unit_name} of {name}. "
        f"Remaining stock: {remaining} {unit_name}."
    )


def receive_stock(name, quantity):
    """Record received stock and increase available quantity."""

    if not isinstance(name, str):
        return "Product name must be text."

    name = name.strip().lower()

    if name not in inventory:
        return f"{name} is not in inventory."

    if (
        isinstance(quantity, bool)
        or not isinstance(quantity, (int, float))
        or not math.isfinite(quantity)
        or quantity <= 0
    ):
        return "Received quantity must be greater than zero."

    inventory[name]["quantity"] += quantity

    save_inventory()

    record_activity(
        "stock_received",
        name,
        quantity,
        inventory[name]["unit"],
        inventory[name]["quantity"],
    )

    remaining = inventory[name]["quantity"]
    unit_name = inventory[name]["unit"]

    return (
        f"Received {quantity} {unit_name} of {name}. "
        f"Current stock: {remaining} {unit_name}."
    )


def check_stock(name):
    """Return the current stock details for one product."""

    if not isinstance(name, str):
        return "Product name must be text."

    name = name.strip().lower()

    if name not in inventory:
        return f"{name} is not in inventory."

    return inventory[name]


def set_reorder_level(name, level):
    """Update the reorder threshold for a product."""

    if not isinstance(name, str):
        return "Product name must be text."

    name = name.strip().lower()

    if name not in inventory:
        return f"{name} is not in inventory."

    if (
        isinstance(level, bool)
        or not isinstance(level, (int, float))
        or not math.isfinite(level)
        or level < 0
    ):
        return "Reorder level cannot be negative."

    inventory[name]["reorder_level"] = level
    save_inventory()

    return f"Reorder level updated for {name}."


def list_low_stock():
    """Return products at or below their reorder levels."""

    return {
        name: details
        for name, details in inventory.items()
        if details["quantity"] <= details["reorder_level"]
    }



def units_match(product, unit):
    """True if no unit was given, or it matches the stored unit.
    Ignores capitals and a trailing 's' so 'packet' matches 'packets'."""

    unit = unit.strip().lower().rstrip("s")

    if not unit:
        return True

    stored_unit = inventory[product]["unit"].strip().lower().rstrip("s")

    return unit == stored_unit


def format_stock(name, details):
    """Turn one product's stock details into a readable line."""

    return (
        f"- {name.title()}: {details['quantity']} {details['unit']} "
        f"(reorder level: {details['reorder_level']})"
    )


def execute_actions(actions):
    """Execute validated actions requested by the AI assistant."""

    results = []

    for action in actions:
        action_type = action["action"]
        # Normalize the product name so lookups are reliable
        product = action.get("product", "").strip().lower()
        quantity = action.get("quantity", 0)
        unit = action.get("unit", "")

        if action_type == "add_product":
            result = add_product(
                product,
                quantity,
                unit,
                action.get("reorder_level", 5),
            )

        elif action_type == "record_sale":
            if product in inventory and not units_match(product, unit):
                result = f"Unit mismatch for {product}."
            else:
                result = record_sale(product, quantity)

        elif action_type == "receive_stock":
            if product in inventory and not units_match(product, unit):
                result = f"Unit mismatch for {product}."
            else:
                result = receive_stock(product, quantity)

        elif action_type == "check_stock":
            details = check_stock(product)
            result = (
                format_stock(product, details) if isinstance(details, dict) else details
            )

        elif action_type == "set_reorder_level":
            result = set_reorder_level(product, quantity)

        elif action_type == "list_low_stock":
            low_items = list_low_stock()

            if low_items:
                result = "Low-stock products:\n" + "\n".join(
                    format_stock(name, details) for name, details in low_items.items()
                )
            else:
                result = "No products are low on stock."

        elif action_type == "get_sales_summary":
            result = get_sales_summary()

        elif action_type == "get_activity_history":
            history = get_activity_history(
                limit=action.get("limit", 10),
                product=product or None,
                action=action.get("filter_action"),
            )

            if not history:
                result = "No matching transactions found."

            else:
                report = ["Recent Inventory Transactions:"]

                for index, item in enumerate(history, start=1):
                    date_value = datetime.fromisoformat(item["date"])
                    formatted_date = date_value.strftime("%d %B %Y")

                    report.append(
                        f"\n{index}. {item['product'].title()}"
                        f"\n   Action: "
                        f"{item['action'].replace('_', ' ').title()}"
                        f"\n   Quantity: {item['quantity']} {item['unit']}"
                        f"\n   Remaining stock: "
                        f"{item['balance_after']} {item['unit']}"
                        f"\n   Date: {formatted_date}"
                    )

                result = "\n".join(report)

        else:
            result = f"Unknown action: {action_type}"

        results.append(str(result))

    return results