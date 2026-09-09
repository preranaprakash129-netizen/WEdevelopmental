"""Multi-turn continuity for `context.conversation_id`.

Process-local and in-memory, which is the right amount of machinery for a
hackathon demo: a single uvicorn worker holds the thread. It is deliberately not
persisted — if we need continuity across restarts or across gateway replicas,
this is the one module to swap for a Postgres-backed store, and nothing above it
changes.
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from dataclasses import dataclass
from typing import Dict, List

# Conversations we keep before evicting the least recently used one. Bounds
# memory on a long-running demo without needing a background sweeper.
MAX_CONVERSATIONS = 200


@dataclass(frozen=True)
class Turn:
    role: str  # "user" | "assistant"
    content: str


class ConversationStore:
    def __init__(self, max_conversations: int = MAX_CONVERSATIONS) -> None:
        self._max_conversations = max_conversations
        self._lock = threading.Lock()
        self._conversations: "OrderedDict[str, List[Turn]]" = OrderedDict()

    def history(self, conversation_id: str, max_turns: int) -> List[Turn]:
        with self._lock:
            turns = self._conversations.get(conversation_id)
            if turns is None:
                return []
            self._conversations.move_to_end(conversation_id)
            return list(turns[-max_turns:])

    def append(self, conversation_id: str, *turns: Turn) -> None:
        with self._lock:
            existing = self._conversations.get(conversation_id)
            if existing is None:
                existing = []
                self._conversations[conversation_id] = existing
            existing.extend(turns)
            self._conversations.move_to_end(conversation_id)
            while len(self._conversations) > self._max_conversations:
                self._conversations.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._conversations.clear()


_store = ConversationStore()


def get_store() -> ConversationStore:
    return _store
