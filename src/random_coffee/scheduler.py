from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from random_coffee.calendar_mock import MockCalendarClient
from random_coffee.config import load_participants, load_schedule
from random_coffee.history import HistoryStore, HistoryWeek
from random_coffee.pairing import generate_pairings


@dataclass(frozen=True)
class SchedulerResult:
    status: str
    week_start: str
    pairing_count: int
    events_path: Path | None


def run_scheduler(
    *,
    participants_path: Path,
    schedule_path: Path,
    history_path: Path,
    output_dir: Path,
    week_start: str | None,
    seed: int | None,
    force: bool,
) -> SchedulerResult:
    target_week = week_start or current_monday()
    effective_seed = seed if seed is not None else int(target_week.replace("-", ""))

    participants = load_participants(participants_path)
    schedule = load_schedule(schedule_path)
    history = HistoryStore.load(history_path)

    if history.has_week(target_week) and not force:
        return SchedulerResult(
            status="skipped", week_start=target_week, pairing_count=0, events_path=None
        )

    pairings = generate_pairings(
        [participant.email for participant in participants],
        previous_pair_keys=history.previous_pair_keys(exclude_week=target_week if force else None),
        seed=effective_seed,
    )
    slots = schedule.resolve_slots(target_week)
    calendar = MockCalendarClient()
    events = [
        calendar.create_event(
            week_start=target_week,
            pairing=pairing,
            slot=slots[index % len(slots)],
            meeting=schedule.meeting,
        )
        for index, pairing in enumerate(pairings)
    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    events_path = output_dir / f"{target_week}.json"
    events_path.write_text(
        json.dumps([event.to_dict() for event in events], indent=2) + "\n",
        encoding="utf-8",
    )

    history.replace_week(
        HistoryWeek(
            week_start=target_week,
            seed=effective_seed,
            status="completed",
            pairings=[
                {
                    "participants": list(pairing.participants),
                    "calendar_event_id": event.event_id,
                    "scheduled_for": event.start.isoformat(),
                }
                for pairing, event in zip(pairings, events, strict=True)
            ],
        )
    )
    history.save()

    return SchedulerResult(
        status="completed",
        week_start=target_week,
        pairing_count=len(pairings),
        events_path=events_path,
    )


def current_monday() -> str:
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    return monday.isoformat()
