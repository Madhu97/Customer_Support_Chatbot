from agentcore_client import AgentCoreHarnessClient


def main():
    client = AgentCoreHarnessClient()

    print("=" * 60)
    print("Customer Support Chatbot")
    print("=" * 60)
    print("Type 'exit' to end.")
    print()

    while True:
        message = input("Customer: ").strip()

        if message.lower() in {
            "exit",
            "quit"
        }:
            break

        if not message:
            continue

        response = client.invoke(
            message
        )

        text = client.extract_text(
            response
        )

        print()
        print("Assistant:", text)
        print()


if __name__ == "__main__":
    main()
