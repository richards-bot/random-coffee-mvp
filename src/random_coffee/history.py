from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class HistoryWeek:
    week_start: str
    seed: int | None
    status: str
    pairings: list[dict[str, Any]]


@dataclass
class HistoryStore:
    path: Path
    weeks: list[HistoryWeek]

    @classmethod
    def load(cls, path: Path) -> "HistoryStore":
        if not path.exists():
            return cls(path=path, weeks=[])
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        weeks_raw = raw.get("weeks", []) if isinstance(raw, dict) else []
        weeks = [
            HistoryWeek(
                week_start=str(week.get("week_start")),
                seed=week.get("seed"),
                status=str(week.get("status", "completed")),
                pairings=list(week.get("pairings", [])),
            )
            for week in weeks_raw
            if isinstance(week, dict)
        ]
        return cls(path=path, weeks=weeks)

    def has_week(self, week_start: str) -> bool:
        return any(week.week_start == week_start for week in self.weeks)

    def previous_pair_keys(self, exclude_week: str | None = None) -> set[tuple[str, str]]:
        keys: set[tuple[str, str]] = set()
        for week in self.weeks:
            if exclude_week is not None and week.week_start == exclude_week:
                continue
            for pairing in week.pairings:
                participants = [str(email).lower() for email in pairing.get("participants", [])]
                for left, right in combinations(sorted(participants), 2):
                    keys.add((left, right))
        return keys

    def replace_week(self, week: HistoryWeek) -> None:
        self.weeks = [existing for existing in self.weeks if existing.week_start != week.week_start]
        self.weeks.append(week)
        self.weeks.sort(key=lambda item: item.week_start)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "weeks": [
                {
                    "week_start": week.week_start,
                    "seed": week.seed,
                    "status": week.status,
                    "pairings": week.pairings,
                }
                for week in self.weeks
            ]
        }
        self.path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
