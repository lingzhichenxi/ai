from __future__ import annotations

from threading import RLock

from .models import UserProfile


class InMemoryProfileStore:
    def __init__(self):
        self._profiles: dict[str, UserProfile] = {}
        self._lock = RLock()

    def get(self, user_id: str) -> UserProfile:
        with self._lock:
            return self._profiles.setdefault(user_id, UserProfile(user_id=user_id))

