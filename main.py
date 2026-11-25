from session_manager import open_previous_session


def main():
    """Display the main menu and route the selected action."""

    print("\n====================================")
    print("       DUKA STOCK ADVISOR")
    print("====================================")

    while True:
        print("\nMAIN MENU")
        print("1. Start a new session")
        print("2. Open a previous session")
        print("3. Exit")

        try:
            choice = input("\nChoose an option (1-3): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if choice == "1":
            from ai_assistant import run_new_session

            run_new_session()
        elif choice == "2":
            open_previous_session()
        elif choice == "3":
            print("\nThank you for using DUKA Stock Advisor!")
            break
        else:
            print("\nInvalid choice. Please select 1, 2, or 3.")


if __name__ == "__main__":
    main()