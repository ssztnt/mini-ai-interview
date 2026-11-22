"""In-memory store for interviews that are still in progress.

Simple by design: state is lost when the server restarts (a documented POC
limitation). Hidden behind a tiny interface so it can be swapped for SQLite or
Redis without touching the service or the API.
"""

from threading import Lock

from app.models import Interview


class InMemoryInterviewRepository:
    def __init__(self) -> None:
        self._items: dict[str, Interview] = {}
        self._lock = Lock()

    def get(self, interview_id: str) -> Interview | None:
        with self._lock:
            return self._items.get(interview_id)

    def save(self, interview: Interview) -> None:
        with self._lock:
            self._items[interview.id] = interview

    def delete(self, interview_id: str) -> None:
        with self._lock:
            self._items.pop(interview_id, None)
