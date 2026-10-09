"""Conversational Memory management for the ReAct Agent."""

from typing import List, Dict, Any
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage


def create_memory() -> MemorySaver:
    """Creates an in-memory checkpointer to persist conversation turns."""
    return MemorySaver()


def get_conversation_history(agent_graph, thread_id: str = "default_session") -> List[BaseMessage]:
    """Retrieves the list of messages in conversational memory for a given thread_id.
    
    Args:
        agent_graph: The compiled LangChain / LangGraph agent graph.
        thread_id: The session identifier.
        
    Returns:
        List of BaseMessage objects recorded in the state.
    """
    config = {"configurable": {"thread_id": thread_id}}
    state = agent_graph.get_state(config)
    if state and state.values and "messages" in state.values:
        return state.values["messages"]
    return []


def clear_session_memory(memory_saver: MemorySaver, thread_id: str = "default_session") -> bool:
    """Deletes conversation memory history for a given thread_id.
    
    Args:
        memory_saver: The MemorySaver instance.
        thread_id: The session identifier to clear.
        
    Returns:
        bool: True if cleared successfully.
    """
    if hasattr(memory_saver, "delete_thread"):
        memory_saver.delete_thread(thread_id)
        return True
    return False
