from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime

from random_coffee.config import MeetingConfig, ResolvedSlot
from random_coffee.pairing import Pairing

RESCHEDULE_NOTE = (
    "If this time does not work, please use Google Calendar's ‘Propose a new time’ "
    "or message each other and move the coffee chat to a better slot."
)


@dataclass(frozen=True)
class MockCalendarEvent:
    event_id: str
    summary: str
    start: datetime
    end: datetime
    attendees: tuple[str, ...]
    description: str
    google_meet_requested: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "summary": self.summary,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "attendees": list(self.attendees),
            "description": self.description,
            "google_meet_requested": self.google_meet_requested,
        }


class MockCalendarClient:
    """Calendar adapter that produces Google Calendar-like event payloads."""

    def create_event(
        self,
        *,
        week_start: str,
        pairing: Pairing,
        slot: ResolvedSlot,
        meeting: MeetingConfig,
    ) -> MockCalendarEvent:
        names = " + ".join(_display_name(email) for email in pairing.participants)
        digest = hashlib.sha1("|".join((week_start, *pairing.participants)).encode()).hexdigest()[:12]
        description = (
            "You’ve been randomly paired for a 15-minute coffee chat this week.\n\n"
            "No agenda or prep needed — just get to know each other.\n\n"
            f"{RESCHEDULE_NOTE}"
        )
        return MockCalendarEvent(
            event_id=f"mock_{week_start}_{digest}",
            summary=meeting.title_template.format(names=names),
            start=slot.start,
            end=slot.end,
            attendees=pairing.participants,
            description=description,
            google_meet_requested=meeting.create_google_meet,
        )


def _display_name(email: str) -> str:
    local = email.split("@", maxsplit=1)[0]
    return local.replace(".", " ").replace("_", " ").replace("-", " ").title()
