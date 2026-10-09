"""Flask Web Server binding Frontend UI with Gemini ReAct Agent & Conversational Memory."""

import json
import os
import sys
from typing import Generator
from flask import Flask, render_template, request, Response, jsonify, stream_with_context
from flask_cors import CORS

from config import get_api_key_or_exit, GEMINI_MODEL, TEMPERATURE, validate_api_key, GEMINI_API_KEY
from agent import GeminiReactAgent, get_conversation_history, clear_session_memory
from tools import ALL_TOOLS

# Initialize Flask application
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Ensure valid API key is present before starting
if not validate_api_key():
    print("\n[!] WARNING: Valid GEMINI_API_KEY not found in .env. Please configure it.")
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "dummy_key"
else:
    api_key = GEMINI_API_KEY

# Initialize the global Gemini ReAct Agent
agent = GeminiReactAgent(
    api_key=api_key,
    model_name=GEMINI_MODEL,
    temperature=TEMPERATURE,
)


@app.route("/")
def index():
    """Renders the main web UI."""
    return render_template("index.html")


@app.route("/api/status", methods=["GET"])
def get_status():
    """Returns current model, tools, and system health status."""
    return jsonify({
        "status": "online",
        "model": agent.model_name,
        "temperature": agent.temperature,
        "tools": [t.name for t in ALL_TOOLS],
        "api_key_configured": validate_api_key(),
    })


@app.route("/api/history/<session_id>", methods=["GET"])
def get_history(session_id: str):
    """Retrieves conversation history from memory checkpointer for a given session."""
    try:
        messages = get_conversation_history(agent.graph, thread_id=session_id)
        formatted = []
        for msg in messages:
            msg_type = type(msg).__name__
            content = ""
            if isinstance(msg.content, str):
                content = msg.content
            elif isinstance(msg.content, list):
                # Extract text chunks
                parts = []
                for p in msg.content:
                    if isinstance(p, str):
                        parts.append(p)
                    elif isinstance(p, dict) and "text" in p:
                        parts.append(p["text"])
                content = "\n".join(parts)

            if msg_type in ("HumanMessage", "user"):
                formatted.append({"role": "user", "content": content})
            elif msg_type in ("AIMessage", "assistant") and content.strip():
                formatted.append({"role": "ai", "content": content})

        return jsonify({"session_id": session_id, "messages": formatted})
    except Exception as exc:
        return jsonify({"error": str(exc), "messages": []}), 500


@app.route("/api/sessions/clear", methods=["POST"])
def clear_session():
    """Clears/resets conversation memory state for a given session."""
    data = request.get_json() or {}
    session_id = data.get("session_id", "default_session")
    success = clear_session_memory(agent.memory, thread_id=session_id)
    return jsonify({"success": success, "session_id": session_id, "message": "Memory reset"})


@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    """Server-Sent Events (SSE) streaming endpoint for live ReAct reasoning steps and final answer."""
    data = request.get_json() or {}
    user_message = data.get("message", "").strip()
    session_id = data.get("session_id", "default_session")

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    def generate_events() -> Generator[str, None, None]:
        try:
            for step in agent.stream_react_turn(user_message, thread_id=session_id):
                payload = json.dumps(step)
                yield f"data: {payload}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as err:
            err_payload = json.dumps({"type": "error", "message": str(err)})
            yield f"data: {err_payload}\n\n"

    return Response(
        stream_with_context(generate_events()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    print("\n" + "=" * 65)
    print("  GEMINI ReAct AGENTIC AI - WEB SERVER STARTING")
    print("=" * 65)
    print(f"  * Local URL   : http://localhost:{port}")
    print(f"  * Model       : {agent.model_name}")
    print(f"  * Tools       : {[t.name for t in ALL_TOOLS]}")
    print("=" * 65 + "\n")
    app.run(host="0.0.0.0", port=port, debug=False)
