# Conversational ReAct Agent powered by Google Gemini & LangChain

An Agentic AI application built using **Python**, **LangChain**, and **Google Gemini**, implementing the **ReAct (Reasoning and Acting)** pattern with stateful **Conversational Memory** and custom tools.

---

## Features

- **Google Gemini Integration**: Uses `langchain-google-genai` with model flexibility (configured to `gemini-3.5-flash` by default).
- **ReAct Pattern**: The agent reasons step-by-step (**Thought** $\rightarrow$ **Action** $\rightarrow$ **Observation** $\rightarrow$ **Final Answer**).
- **Conversational Memory**: Stateful session-based memory using LangGraph's checkpointer (`MemorySaver`). The agent remembers context, prior answers, and references across multiple conversation turns.
- **Tools**:
  - `calculator`: Safe mathematical evaluator (arithmetic, percentages, square roots, trigonometry, logarithms, etc.) built with AST parsing.
  - `web_search`: Live search powered by DuckDuckGo (`ddgs`) for real-time information and facts.
  - `local_date_time`: Provides current local date, time, weekday, and system timezone.
- **Interactive CLI & REPL**: Beautiful terminal interface showing intermediate ReAct thoughts, actions, and observations.

---

## Project Structure

```
RAGD3_1/
├── .env                  # Environment variables (Your GEMINI_API_KEY goes here)
├── .env.example          # Environment variable template
├── requirements.txt      # Python dependencies
├── config.py             # Settings and API key validation
├── tools/
│   ├── __init__.py       # Tools registry
│   ├── calculator.py     # Safe math calculation tool (AST-based)
│   ├── web_search.py     # Live DuckDuckGo search tool
│   └── local_datetime.py # Local date, time, and timezone tool
├── agent/
│   ├── __init__.py       # Agent module exports
│   ├── prompts.py        # ReAct system prompt and instructions
│   ├── memory.py         # Conversational memory state management
│   └── react_agent.py    # ReAct agent builder and step streaming
├── templates/
│   └── index.html        # Modern Glassmorphic Web UI
├── static/
│   ├── css/style.css     # Styling for chat bubbles & ReAct accordions
│   └── js/app.js         # Frontend SSE streaming & session controller
├── app.py                # Flask Web Server (REST + SSE streaming)
├── main.py               # Interactive CLI chat application
├── test_agent.py         # Automated test and verification script
└── README.md             # Project documentation
```

---

## Quick Start Guide

### 1. Configure Your Gemini API Key
Ensure your Google Gemini API key is configured in [.env](file:///c:/Users/elaya/Desktop/Yellowmatics/Agentic%20AI/RAGD3_1/.env):

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Beautiful Web UI 🌐
```bash
python app.py
```
Open your browser at **`http://localhost:5000`** to interact with the visual ReAct dashboard, live execution accordions, and session history!

### 4. Or Run via Terminal CLI 💻
```bash
python main.py
```

---

## Interactive CLI Commands

While in the chat interface:
- Type your prompt and press `Enter`.
- `/history` : View all messages currently stored in conversational memory.
- `/clear`   : Reset conversation memory and start a fresh session thread.
- `/session <id>` : Switch to or create a specific conversation session thread.
- `/help`    : Display the help banner.
- `exit` or `quit` : Exit the program.

---

## Example ReAct Conversation Flow

```text
[session_a1b2c3] You > What is today's date, and what is 250 raised to the power of 2?

⚡ [ReAct Action #1]: Calling `local_date_time` with arguments: {}
👁️ [ReAct Observation from `local_date_time`]:
   Current Local Date & Time: 2026-10-08 15:25:54
   Day of the Week: Thursday
   Timezone: India Standard Time (UTC+0530)

⚡ [ReAct Action #2]: Calling `calculator` with arguments: {'expression': '250 ** 2'}
👁️ [ReAct Observation from `calculator`]:
   62500

🤖 [Gemini Agent]:
Today's date is Thursday, October 8, 2026.
250 raised to the power of 2 (250²) is 62,500.

[session_a1b2c3] You > Now divide that number by 5.

⚡ [ReAct Action #1]: Calling `calculator` with arguments: {'expression': '62500 / 5'}
👁️ [ReAct Observation from `calculator`]:
   12500

🤖 [Gemini Agent]:
Dividing 62,500 by 5 gives 12,500.
```
*(Notice how the agent references "that number" seamlessly using Conversational Memory!)*
