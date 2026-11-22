"""Completed interviews are stored as one pretty-printed JSON file each.

Human-readable on purpose: reviewers can open `data/interviews/*.json` and see
exactly what was captured. File names start with the completion date so they
sort chronologically: ``2026-11-22_ab12cd34ef56.json``.
"""

import logging
from pathlib import Path

from pydantic import ValidationError

from app.models import Interview

logger = logging.getLogger(__name__)


class JsonInterviewStore:
    def __init__(self, directory: Path) -> None:
        self._dir = directory
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, interview: Interview) -> Path:
        stamp = (interview.completed_at or interview.created_at).strftime("%Y-%m-%d")
        return self._dir / f"{stamp}_{interview.id}.json"

    def save(self, interview: Interview) -> Path:
        path = self._path_for(interview)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(interview.model_dump_json(indent=2), encoding="utf-8")
        tmp.replace(path)  # atomic: never leaves a half-written file
        return path

    def get(self, interview_id: str) -> Interview | None:
        for path in self._dir.glob(f"*{interview_id}.json"):
            interview = self._load(path)
            if interview and interview.id == interview_id:
                return interview
        return None

    def list(self) -> list[Interview]:
        interviews = [i for p in self._dir.glob("*.json") if (i := self._load(p))]
        return sorted(interviews, key=lambda i: i.completed_at or i.created_at, reverse=True)

    @staticmethod
    def _load(path: Path) -> Interview | None:
        try:
            return Interview.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValidationError) as exc:
            logger.warning("Skipping unreadable interview file %s: %s", path.name, exc)
            return None
