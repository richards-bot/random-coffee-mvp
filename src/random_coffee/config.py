from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml


class ConfigError(ValueError):
    """Raised when repository YAML config is invalid."""


@dataclass(frozen=True)
class Participant:
    email: str
    name: str
    active: bool = True


@dataclass(frozen=True)
class SlotConfig:
    day: str
    time: str


@dataclass(frozen=True)
class ResolvedSlot:
    start: datetime
    end: datetime


@dataclass(frozen=True)
class MeetingConfig:
    duration_minutes: int
    title_template: str
    create_google_meet: bool


@dataclass(frozen=True)
class ScheduleConfig:
    timezone: str
    meeting: MeetingConfig
    slots: tuple[SlotConfig, ...]

    def resolve_slots(self, week_start: str) -> list[ResolvedSlot]:
        start_date = date.fromisoformat(week_start)
        if start_date.weekday() != 0:
            raise ConfigError("week_start must be a Monday ISO date")

        tz = ZoneInfo(self.timezone)
        resolved: list[ResolvedSlot] = []
        for slot in self.slots:
            slot_date = start_date + timedelta(days=_day_offset(slot.day))
            hour, minute = _parse_hhmm(slot.time)
            start = datetime.combine(slot_date, time(hour, minute), tzinfo=tz)
            end = start + timedelta(minutes=self.meeting.duration_minutes)
            resolved.append(ResolvedSlot(start=start, end=end))
        return resolved


def load_participants(path: Path) -> list[Participant]:
    raw = _load_yaml_mapping(path)
    entries = raw.get("participants")
    if not isinstance(entries, list):
        raise ConfigError("participants.yaml must contain a participants list")

    participants: list[Participant] = []
    seen_active: set[str] = set()
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise ConfigError(f"participant #{index} must be a mapping")
        email = _normalise_email(entry.get("email"))
        name = str(entry.get("name") or email).strip()
        active = bool(entry.get("active", True))
        if active:
            if email in seen_active:
                raise ConfigError(f"Duplicate active participant email: {email}")
            seen_active.add(email)
            participants.append(Participant(email=email, name=name, active=True))
    if len(participants) < 2:
        raise ConfigError("At least two active participants are required")
    return participants


def load_schedule(path: Path) -> ScheduleConfig:
    raw = _load_yaml_mapping(path)
    meeting_raw = raw.get("meeting")
    slots_raw = raw.get("slots")
    if not isinstance(meeting_raw, dict):
        raise ConfigError("schedule.yaml must contain meeting settings")
    if not isinstance(slots_raw, list) or not slots_raw:
        raise ConfigError("schedule.yaml must contain at least one slot")

    duration = int(meeting_raw.get("duration_minutes", 15))
    if duration <= 0:
        raise ConfigError("meeting.duration_minutes must be positive")

    slots: list[SlotConfig] = []
    for index, slot_raw in enumerate(slots_raw, start=1):
        if not isinstance(slot_raw, dict):
            raise ConfigError(f"slot #{index} must be a mapping")
        day = str(slot_raw.get("day") or "").strip()
        slot_time = str(slot_raw.get("time") or "").strip()
        _day_offset(day)
        _parse_hhmm(slot_time)
        slots.append(SlotConfig(day=day, time=slot_time))

    return ScheduleConfig(
        timezone=str(raw.get("timezone") or "Europe/London"),
        meeting=MeetingConfig(
            duration_minutes=duration,
            title_template=str(meeting_raw.get("title_template") or "Random Coffee: {names}"),
            create_google_meet=bool(meeting_raw.get("create_google_meet", True)),
        ),
        slots=tuple(slots),
    )


def _load_yaml_mapping(path: Path) -> dict:
    if not path.exists():
        raise ConfigError(f"Missing config file: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"{path} must contain a YAML mapping")
    return data


def _normalise_email(value: object) -> str:
    email = str(value or "").strip().lower()
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise ConfigError(f"Invalid participant email: {value!r}")
    return email


def _day_offset(day: str) -> int:
    offsets = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    key = day.strip().lower()
    if key not in offsets:
        raise ConfigError(f"Invalid slot day: {day!r}")
    return offsets[key]


def _parse_hhmm(value: str) -> tuple[int, int]:
    try:
        hour_text, minute_text = value.split(":", maxsplit=1)
        hour = int(hour_text)
        minute = int(minute_text)
    except ValueError as exc:
        raise ConfigError(f"Invalid slot time: {value!r}") from exc
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ConfigError(f"Invalid slot time: {value!r}")
    return hour, minute
