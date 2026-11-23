from ai_assistant import AIAssistant
from inventory import InventoryManager
from session_manager import SessionManager


def print_menu() -> None:
    print("\n=== Retail Inventory & AI CLI ===")
    print("1. Add / Restock Product")
    print("2. Record Sale")
    print("3. View Inventory & Totals")
    print("4. Ask Gemini AI Assistant")
    print("5. Clear Chat History")
    print("6. Exit")


def main() -> None:
    inventory = InventoryManager()
    sessions = SessionManager()
    assistant = AIAssistant()

    while True:
        print_menu()
        choice = input("Select an option (1-6): ").strip()

        try:
            if choice == "1":
                sku = input("SKU: ").strip()
                name = input("Product Name: ").strip()
                price = float(input("Unit Price: ").strip())
                qty = int(input("Quantity: ").strip())
                prod = inventory.add_product(sku, name, price, qty)
                print(f"Saved: [{prod.sku}] {prod.name} — {prod.quantity} units @ ${prod.price:.2f}")

            elif choice == "2":
                sku = input("SKU sold: ").strip()
                qty = int(input("Quantity sold: ").strip())
                sale = inventory.record_sale(sku, qty)
                print(f"Recorded sale: {sale['quantity']}x {sale['name']} (${sale['total']:.2f})")

            elif choice == "3":
                print("\n--- Current Stock ---")
                print(inventory.to_context_summary())

            elif choice == "4":
                question = input("Ask Gemini: ").strip()
                if not question:
                    continue
                reply = assistant.ask(
                    user_message=question,
                    inventory_context=inventory.to_context_summary(),
                    past_history=sessions.history,
                )
                print(f"\nGemini:\n{reply}")
                sessions.append_turn("user", question)
                sessions.append_turn("assistant", reply)

            elif choice == "5":
                sessions.clear()
                print("Chat history cleared.")

            elif choice == "6":
                print("Goodbye!")
                break

            else:
                print("Invalid choice. Please pick 1-6.")

        except (ValueError, KeyError, EnvironmentError) as exc:
            print(f"Error: {exc}")


if __name__ == "__main__":
    main()
