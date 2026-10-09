"""Automated test suite and sanity checks for the Gemini ReAct Agent."""

import sys
from config import validate_api_key, GEMINI_API_KEY, GEMINI_MODEL
from tools import calculator, web_search, local_date_time
from agent import GeminiReactAgent, get_conversation_history


def test_tools():
    """Tests the three required tools independently."""
    print("\n--- 1. Testing Tools Independently ---")

    # Test Calculator
    calc_res = calculator.invoke({"expression": "(15 * 4) + sqrt(144) - (50 / 2)"})
    print(f"[*] Calculator test result: {calc_res}")
    assert "47" in str(calc_res), f"Calculator unexpected result: {calc_res}"

    # Test Local Date Time
    dt_res = local_date_time.invoke({})
    print(f"[*] Local Date Time test result:\n{dt_res}")
    assert "Date & Time" in dt_res, "Date time tool missing expected header"

    # Test Web Search (DuckDuckGo)
    search_res = web_search.invoke({"query": "Python programming language", "max_results": 2})
    print(f"[*] Web Search snippet preview:\n{search_res[:150]}...")
    assert len(search_res) > 20, "Web search returned unexpectedly short response"

    print("[SUCCESS] All 3 tools passed standalone tests!\n")


def test_agent_with_api_key():
    """Tests end-to-end ReAct agent execution and conversational memory."""
    print("--- 2. Testing End-to-End ReAct Agent & Memory ---")
    if not validate_api_key():
        print("[SKIP] No valid GEMINI_API_KEY found in .env.")
        print("       Once you add your key to `.env`, re-run this script to test live API calls.")
        return

    agent = GeminiReactAgent(api_key=GEMINI_API_KEY, model_name=GEMINI_MODEL)
    test_session = "test_memory_session_1"

    print("\n[Turn 1] Asking agent a calculation and storing in memory...")
    turn1_prompt = "My favorite number is 7. Multiply it by 9 and tell me the result."
    print(f"User: {turn1_prompt}")
    for step in agent.stream_react_turn(turn1_prompt, thread_id=test_session):
        if step["type"] == "action":
            print(f"  -> Agent invoked tool: {step['tool']} with {step['args']}")
        elif step["type"] == "observation":
            print(f"  -> Observation: {step['result']}")
        elif step["type"] == "answer":
            print(f"Agent: {step['content']}\n")

    print("[Turn 2] Testing conversational memory recall (referencing favorite number without re-stating it)...")
    turn2_prompt = "Now add 100 to my favorite number."
    print(f"User: {turn2_prompt}")
    for step in agent.stream_react_turn(turn2_prompt, thread_id=test_session):
        if step["type"] == "action":
            print(f"  -> Agent invoked tool: {step['tool']} with {step['args']}")
        elif step["type"] == "observation":
            print(f"  -> Observation: {step['result']}")
        elif step["type"] == "answer":
            print(f"Agent: {step['content']}\n")

    history = get_conversation_history(agent.graph, thread_id=test_session)
    print(f"[*] Conversational memory length: {len(history)} messages.")
    assert len(history) >= 4, "Conversational memory did not record multi-turn history properly!"
    print("[SUCCESS] End-to-end ReAct agent and Conversational Memory verified!\n")


if __name__ == "__main__":
    test_tools()
    test_agent_with_api_key()
