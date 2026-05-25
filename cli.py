import os

from agent.agent import MCPAgent


def main():
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    print("Starting MCP server and loading knowledge base...")
    agent = MCPAgent()
    print("Agent ready. Type 'exit' to quit.\n")

    history: list[dict] = []

    while True:
        try:
            q = input("Ask: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if q.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        if not q:
            continue

        history.append({"role": "user", "content": q})
        try:
            answer = agent.invoke(list(history))
            print(f"\n{answer}\n")
            history.append({"role": "assistant", "content": answer})
        except Exception as e:
            print(f"Error: {e}\n")
            history.pop()


if __name__ == "__main__":
    main()