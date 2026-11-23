SYSTEM_INSTRUCTION = """You are a sharp, practical retail and inventory operations assistant.
Answer questions using ONLY the provided live inventory and sales context when referencing stock levels, prices, or SKUs.
If an item is missing from the inventory context, state clearly that it is not in stock rather than guessing.
Keep responses concise, actionable, and easy to scan in a terminal."""


def build_inventory_prompt(user_message: str, inventory_context: str) -> str:
    return (
        f"CURRENT INVENTORY SNAPSHOT:\n{inventory_context}\n\n"
        f"USER REQUEST:\n{user_message}"
    )
