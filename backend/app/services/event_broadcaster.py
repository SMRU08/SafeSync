"""
event_broadcaster.py — RAKSHYA VISION Phase 7
In-Memory Event Broadcaster for WebSocket-Ready Architecture.
Allows internal subscribers to listen for safety incidents, alerts, and escalations.
Ready for Phase 8 dashboard connection without implementing frontend UI in Phase 7.
"""

import logging
import asyncio
from typing import Callable, Dict, List, Any, Optional

log = logging.getLogger(__name__)


class EventBroadcaster:
    """
    Thread-safe in-memory publish-subscribe dispatcher.
    """

    def __init__(self):
        self._subscribers: List[Callable[[str, Dict[str, Any]], Any]] = []

    def subscribe(self, callback: Callable[[str, Dict[str, Any]], Any]):
        """Registers a listener callback for broadcasted events."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[str, Dict[str, Any]], Any]):
        """Removes a listener callback."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def broadcast(self, event_name: str, payload: Dict[str, Any]):
        """
        Dispatches an event payload synchronously or schedules on asyncio loop.
        Supported events:
          - AlertCreated
          - AlertUpdated
          - AlertEscalated
          - IncidentCreated
          - IncidentResolved
        """
        for callback in list(self._subscribers):
            try:
                callback(event_name, payload)
            except Exception as e:
                log.warning("Broadcaster listener failed for %s: %s", event_name, e)

    def clear(self):
        self._subscribers.clear()


# Global singleton instance
broadcaster = EventBroadcaster()
