from __future__ import annotations

from pathlib import Path

import pytest

from random_coffee.config import ConfigError, load_participants, load_schedule
from random_coffee.history import HistoryStore
from random_coffee.pairing import generate_pairings
from random_coffee.scheduler import run_scheduler


def write_yaml(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_participants(n: int) -> str:
    rows = ["participants:"]
    for i in range(1, n + 1):
        rows.extend(
            [
                f"  - email: person{i:02d}@example.com",
                f"    name: Person {i:02d}",
                "    active: true",
            ]
        )
    return "\n".join(rows) + "\n"


def schedule_yaml() -> str:
    return """
timezone: Europe/London
meeting:
  duration_minutes: 15
  title_template: "Random Coffee: {names}"
  create_google_meet: true
slots:
  - day: Tuesday
    time: "10:00"
  - day: Tuesday
    time: "14:30"
  - day: Wednesday
    time: "10:00"
  - day: Wednesday
    time: "15:00"
  - day: Thursday
    time: "11:00"
  - day: Thursday
    time: "14:00"
"""


def test_load_participants_normalises_and_rejects_duplicate_active_emails(tmp_path: Path) -> None:
    participants_path = tmp_path / "participants.yaml"
    write_yaml(
        participants_path,
        """
participants:
  - email: " Alice@Example.com "
    name: Alice
    active: true
  - email: alice@example.com
    name: Alice Duplicate
    active: true
""",
    )

    with pytest.raises(ConfigError, match="Duplicate active participant email"):
        load_participants(participants_path)


def test_generate_pairings_creates_25_unique_pairs_for_50_people() -> None:
    participants = [f"person{i:02d}@example.com" for i in range(1, 51)]

    pairings = generate_pairings(participants, previous_pair_keys=set(), seed=1234)

    assert len(pairings) == 25
    flattened = [email for pairing in pairings for email in pairing.participants]
    assert sorted(flattened) == participants
    assert all(len(pairing.participants) == 2 for pairing in pairings)


def test_generate_pairings_avoids_previous_pair_when_alternative_exists() -> None:
    participants = ["alice@example.com", "bob@example.com", "cara@example.com", "dev@example.com"]
    previous = {("alice@example.com", "bob@example.com")}

    pairings = generate_pairings(participants, previous_pair_keys=previous, seed=1)

    actual_pair_keys = {pairing.key for pairing in pairings}
    assert ("alice@example.com", "bob@example.com") not in actual_pair_keys


def test_generate_pairings_uses_one_group_of_three_for_odd_counts() -> None:
    participants = [f"person{i:02d}@example.com" for i in range(1, 6)]

    pairings = generate_pairings(participants, previous_pair_keys=set(), seed=42)

    assert sorted(len(pairing.participants) for pairing in pairings) == [2, 3]
    flattened = [email for pairing in pairings for email in pairing.participants]
    assert sorted(flattened) == participants


def test_scheduler_writes_history_and_mock_events_for_new_week(tmp_path: Path) -> None:
    participants_path = tmp_path / "config" / "participants.yaml"
    schedule_path = tmp_path / "config" / "schedule.yaml"
    history_path = tmp_path / "data" / "history.yaml"
    output_dir = tmp_path / "output" / "mock-calendar-events"
    write_yaml(participants_path, make_participants(50))
    write_yaml(schedule_path, schedule_yaml())
    write_yaml(history_path, "weeks: []\n")

    result = run_scheduler(
        participants_path=participants_path,
        schedule_path=schedule_path,
        history_path=history_path,
        output_dir=output_dir,
        week_start="2026-06-08",
        seed=12345,
        force=False,
    )

    assert result.status == "completed"
    assert result.pairing_count == 25
    events_path = output_dir / "2026-06-08.json"
    assert events_path.exists()
    history = HistoryStore.load(history_path)
    assert history.has_week("2026-06-08")
    events_text = events_path.read_text(encoding="utf-8")
    assert "If this time does not work" in events_text
    assert "mock_2026-06-08_" in events_text


def test_scheduler_is_idempotent_for_existing_week(tmp_path: Path) -> None:
    participants_path = tmp_path / "config" / "participants.yaml"
    schedule_path = tmp_path / "config" / "schedule.yaml"
    history_path = tmp_path / "data" / "history.yaml"
    output_dir = tmp_path / "output" / "mock-calendar-events"
    write_yaml(participants_path, make_participants(50))
    write_yaml(schedule_path, schedule_yaml())
    write_yaml(history_path, "weeks: []\n")

    first = run_scheduler(
        participants_path=participants_path,
        schedule_path=schedule_path,
        history_path=history_path,
        output_dir=output_dir,
        week_start="2026-06-08",
        seed=12345,
        force=False,
    )
    second = run_scheduler(
        participants_path=participants_path,
        schedule_path=schedule_path,
        history_path=history_path,
        output_dir=output_dir,
        week_start="2026-06-08",
        seed=99999,
        force=False,
    )

    assert first.status == "completed"
    assert second.status == "skipped"
    history = HistoryStore.load(history_path)
    assert len(history.weeks) == 1


def test_load_schedule_calculates_london_slot_datetimes(tmp_path: Path) -> None:
    schedule_path = tmp_path / "schedule.yaml"
    write_yaml(schedule_path, schedule_yaml())

    schedule = load_schedule(schedule_path)
    slots = schedule.resolve_slots("2026-06-08")

    assert slots[0].start.isoformat() == "2026-06-09T10:00:00+01:00"
    assert slots[0].end.isoformat() == "2026-06-09T10:15:00+01:00"
    assert slots[-1].start.isoformat() == "2026-06-11T14:00:00+01:00"
