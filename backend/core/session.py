"""
In-memory session store.

Maps session_id → ordered list of message dicts.
Each dict is:  {"role": "user"|"assistant", "content": str | list}

Content is a list when the turn contained multimodal data (images).
Both formats are compatible with the Groq/OpenAI chat API.
"""

from collections import defaultdict
from typing import List


_sessions: dict[str, list] = defaultdict(list)


def get_history(session_id: str) -> List[dict]:
    """Return full chat history for a session (empty list if new)."""
    return list(_sessions[session_id])


def append_turn(session_id: str, role: str, content) -> None:
    """Append one turn.  content is str for text or list for multimodal."""
    _sessions[session_id].append({"role": role, "content": content})


def clear_session(session_id: str) -> None:
    """Delete all history for a session."""
    _sessions[session_id] = []


def list_sessions() -> List[str]:
    return list(_sessions.keys())
