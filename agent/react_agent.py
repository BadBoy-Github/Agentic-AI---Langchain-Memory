"""ReAct Agent powered by Google Gemini, LangChain, and Conversational Memory."""

from typing import Generator, Dict, Any, Optional, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage
from langgraph.checkpoint.memory import MemorySaver

# Use modern langchain.agents.create_agent or fallback to langgraph.prebuilt.create_react_agent
try:
    from langchain.agents import create_agent
    _CREATE_AGENT_FN = "langchain"
except ImportError:
    from langgraph.prebuilt import create_react_agent as create_agent  # type: ignore
    _CREATE_AGENT_FN = "langgraph"

from tools import ALL_TOOLS
from agent.prompts import REACT_SYSTEM_PROMPT
from agent.memory import create_memory


def _extract_text_content(content: Any) -> str:
    """Extracts plain text content from string or structured list format."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
            elif hasattr(item, "text"):
                parts.append(getattr(item, "text"))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


class GeminiReactAgent:
    """Conversational ReAct Agent powered by Google Gemini and LangChain."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-3.5-flash",
        temperature: float = 0.0,
        memory: Optional[MemorySaver] = None,
        tools: Optional[list] = None,
    ):
        """Initializes the Gemini ReAct agent with tools and conversational memory.

        Args:
            api_key: The Google Gemini API key.
            model_name: The Gemini model name (default: 'gemini-3.5-flash').
            temperature: Sampling temperature for reasoning (default: 0.0).
            memory: Optional custom MemorySaver checkpointer.
            tools: Optional list of custom tools (defaults to ALL_TOOLS).
        """
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.memory = memory or create_memory()
        self.tools = tools or ALL_TOOLS

        # Initialize Google Gemini Chat Model
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            api_key=self.api_key,
            temperature=self.temperature,
        )

        # Build compiled ReAct Agent graph
        if _CREATE_AGENT_FN == "langchain":
            self.graph = create_agent(
                model=self.llm,
                tools=self.tools,
                checkpointer=self.memory,
                system_prompt=REACT_SYSTEM_PROMPT,
            )
        else:
            self.graph = create_agent(
                model=self.llm,
                tools=self.tools,
                checkpointer=self.memory,
                prompt=REACT_SYSTEM_PROMPT,
            )

    def stream_react_turn(
        self,
        user_message: str,
        thread_id: str = "default_session",
    ) -> Generator[Dict[str, Any], None, str]:
        """Streams each reasoning step of the ReAct loop (Thought/Action, Observation, Answer).

        Args:
            user_message: The text input from the user.
            thread_id: Unique identifier for the conversation session.

        Yields:
            Dict containing step information:
              - type: 'action' | 'observation' | 'answer'
              - data: details of the step
        
        Returns:
            The final answer string.
        """
        config = {"configurable": {"thread_id": thread_id}}
        input_payload = {"messages": [HumanMessage(content=user_message)]}
        final_answer = ""

        # Stream updates from graph execution
        for event in self.graph.stream(input_payload, config=config, stream_mode="updates"):
            for node_name, node_output in event.items():
                messages: List[BaseMessage] = node_output.get("messages", [])
                for msg in messages:
                    # Model node output: either tool calls (Actions) or Final Answer
                    if isinstance(msg, AIMessage):
                        if getattr(msg, "tool_calls", None):
                            for call in msg.tool_calls:
                                yield {
                                    "type": "action",
                                    "tool": call.get("name"),
                                    "args": call.get("args"),
                                    "id": call.get("id"),
                                }
                        if msg.content:
                            extracted = _extract_text_content(msg.content)
                            if extracted.strip():
                                final_answer = extracted
                                # Yield intermediate thought if it also had tool calls
                                if getattr(msg, "tool_calls", None):
                                    yield {
                                        "type": "thought",
                                        "content": extracted,
                                    }

                    # Tool execution node output: Observations
                    elif isinstance(msg, ToolMessage):
                        yield {
                            "type": "observation",
                            "tool": getattr(msg, "name", "unknown_tool"),
                            "result": str(msg.content),
                            "tool_call_id": getattr(msg, "tool_call_id", ""),
                        }

        if final_answer:
            yield {
                "type": "answer",
                "content": final_answer,
            }

        return final_answer

    def chat(self, user_message: str, thread_id: str = "default_session") -> str:
        """Executes a complete synchronous turn and returns the final response.

        Args:
            user_message: The text input from the user.
            thread_id: The session identifier for conversational memory.

        Returns:
            The assistant's final response string.
        """
        config = {"configurable": {"thread_id": thread_id}}
        result = self.graph.invoke(
            {"messages": [HumanMessage(content=user_message)]},
            config=config,
        )
        messages = result.get("messages", [])
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content:
                return _extract_text_content(msg.content)
        return ""
