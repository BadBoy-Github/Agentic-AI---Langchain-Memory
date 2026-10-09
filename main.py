"""Interactive CLI for the Gemini ReAct Conversational Agent."""

import sys
import uuid
from config import get_api_key_or_exit, GEMINI_MODEL, TEMPERATURE
from agent import GeminiReactAgent, get_conversation_history


def print_banner(model_name: str, session_id: str):
    """Prints a friendly application banner."""
    print("=" * 70)
    print("  GEMINI ReAct AGENTIC AI (LangChain + Conversational Memory)")
    print("=" * 70)
    print(f"  * Engine      : Google Gemini ({model_name})")
    print(f"  * Architecture: ReAct (Reasoning + Acting Pattern)")
    print(f"  * Memory      : Multi-Turn Conversational Memory Enabled")
    print(f"  * Tools       : [1] Calculator")
    print(f"                  [2] Web Search (DuckDuckGo)")
    print(f"                  [3] Local Date & Time")
    print(f"  * Session ID  : {session_id}")
    print("=" * 70)
    print("Commands:")
    print("  /help           - Show help & instructions")
    print("  /history        - Show conversation turns currently in memory")
    print("  /clear          - Reset conversation memory (starts new session)")
    print("  /session <id>   - Switch to a different session thread")
    print("  exit / quit     - Exit the application")
    print("=" * 70 + "\n")


def display_history(agent: GeminiReactAgent, thread_id: str):
    """Displays the current conversation history stored in memory."""
    messages = get_conversation_history(agent.graph, thread_id=thread_id)
    if not messages:
        print(f"\n[Memory]: No previous messages found for session '{thread_id}'.\n")
        return

    print(f"\n--- Conversation History for Session '{thread_id}' ({len(messages)} messages) ---")
    for idx, msg in enumerate(messages, 1):
        msg_type = type(msg).__name__
        content_preview = str(msg.content).strip()
        if len(content_preview) > 120:
            content_preview = content_preview[:117] + "..."
        print(f"[{idx}] {msg_type}: {content_preview}")
    print("--------------------------------------------------------------------\n")


def run_react_turn(agent: GeminiReactAgent, user_prompt: str, thread_id: str):
    """Runs a single user query through the ReAct agent with step visualization."""
    print()
    action_count = 0
    final_answer = ""

    try:
        for step in agent.stream_react_turn(user_prompt, thread_id=thread_id):
            step_type = step.get("type")

            if step_type == "thought":
                # Intermediate model reasoning text
                thought_text = step.get("content", "").strip()
                if thought_text:
                    print(f"\n🤔 [ReAct Thought]: {thought_text}")

            elif step_type == "action":
                action_count += 1
                tool_name = step.get("tool")
                tool_args = step.get("args")
                print(f"\n⚡ [ReAct Action #{action_count}]: Calling `{tool_name}` with arguments:")
                print(f"   --> {tool_args}")

            elif step_type == "observation":
                tool_name = step.get("tool")
                result_text = step.get("result", "").strip()
                # Truncate very long observation for display if needed
                display_result = result_text if len(result_text) <= 500 else result_text[:497] + "..."
                print(f"\n👁️ [ReAct Observation from `{tool_name}`]:")
                for line in display_result.splitlines():
                    print(f"   {line}")

            elif step_type == "answer":
                final_answer = step.get("content", "")

        # Print final formatted response
        print("\n" + "-" * 70)
        print("🤖 [Gemini Agent]:")
        print(final_answer if final_answer else "(No response generated)")
        print("-" * 70 + "\n")

    except KeyboardInterrupt:
        print("\n[!] Turn cancelled by user.\n")
    except Exception as exc:
        print(f"\n[!] Error during agent execution: {str(exc)}\n")


def main():
    """Main CLI entrypoint."""
    # Ensure Gemini API key is configured
    api_key = get_api_key_or_exit()

    # Create conversational agent
    session_id = f"session_{uuid.uuid4().hex[:6]}"
    agent = GeminiReactAgent(
        api_key=api_key,
        model_name=GEMINI_MODEL,
        temperature=TEMPERATURE,
    )

    print_banner(agent.model_name, session_id)

    while True:
        try:
            user_input = input(f"[{session_id}] You > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting. Goodbye!")
            sys.exit(0)

        if not user_input:
            continue

        lower_input = user_input.lower()

        if lower_input in ("exit", "quit", "q"):
            print("Exiting. Goodbye!")
            break

        if lower_input == "/help":
            print_banner(agent.model_name, session_id)
            continue

        if lower_input == "/history":
            display_history(agent, session_id)
            continue

        if lower_input == "/clear":
            session_id = f"session_{uuid.uuid4().hex[:6]}"
            print(f"\n[Memory]: Memory reset. New session started: '{session_id}'\n")
            continue

        if lower_input.startswith("/session"):
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1 and parts[1].strip():
                session_id = parts[1].strip()
                print(f"\n[Memory]: Switched to session: '{session_id}'\n")
            else:
                print(f"\nCurrent session ID: '{session_id}'. Usage: /session <id>\n")
            continue

        # Execute ReAct conversation turn
        run_react_turn(agent, user_input, session_id)


if __name__ == "__main__":
    main()
