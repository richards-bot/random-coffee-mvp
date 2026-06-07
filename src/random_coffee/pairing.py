from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from random import Random


@dataclass(frozen=True)
class Pairing:
    participants: tuple[str, ...]

    @property
    def key(self) -> tuple[str, ...]:
        return tuple(sorted(self.participants))

    def two_person_keys(self) -> set[tuple[str, str]]:
        keys: set[tuple[str, str]] = set()
        for left, right in combinations(self.participants, 2):
            key = (left, right) if left <= right else (right, left)
            keys.add(key)
        return keys


def generate_pairings(
    participants: list[str],
    previous_pair_keys: set[tuple[str, str]],
    seed: int,
    max_attempts: int = 2_000,
) -> list[Pairing]:
    """Generate deterministic, history-aware random pairings.

    The search samples seeded shuffles and keeps the arrangement with the fewest
    repeated historical pair keys. With 50 participants and sparse history this
    reliably finds a zero-repeat week while remaining simple for the MVP.
    """

    normalised = sorted({email.strip().lower() for email in participants})
    if len(normalised) != len(participants):
        raise ValueError("participants must be unique before pairing")
    if len(normalised) < 2:
        raise ValueError("at least two participants are required")

    rng = Random(seed)
    best_pairings: list[Pairing] | None = None
    best_score: tuple[int, int] | None = None

    for _ in range(max_attempts):
        shuffled = normalised[:]
        rng.shuffle(shuffled)
        pairings = _pair_shuffled(shuffled)
        repeat_count = sum(
            1
            for pairing in pairings
            for key in pairing.two_person_keys()
            if key in previous_pair_keys
        )
        group_of_three_count = sum(1 for pairing in pairings if len(pairing.participants) == 3)
        score = (repeat_count, group_of_three_count)
        if best_score is None or score < best_score:
            best_score = score
            best_pairings = pairings
        if repeat_count == 0:
            break

    if best_pairings is None:
        raise RuntimeError("failed to generate pairings")
    return best_pairings


def _pair_shuffled(shuffled: list[str]) -> list[Pairing]:
    pairings: list[Pairing] = []
    remaining = shuffled[:]

    if len(remaining) % 2 == 1:
        group = tuple(sorted(remaining[:3]))
        pairings.append(Pairing(participants=group))
        remaining = remaining[3:]

    for index in range(0, len(remaining), 2):
        pairings.append(Pairing(participants=tuple(sorted(remaining[index : index + 2]))))
    return pairings
