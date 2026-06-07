from __future__ import annotations

import argparse
from pathlib import Path

from random_coffee.scheduler import run_scheduler


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate weekly random coffee pairings")
    parser.add_argument("--participants", type=Path, default=Path("config/participants.yaml"))
    parser.add_argument("--schedule", type=Path, default=Path("config/schedule.yaml"))
    parser.add_argument("--history", type=Path, default=Path("data/history.yaml"))
    parser.add_argument(
        "--output-dir", type=Path, default=Path("output/mock-calendar-events")
    )
    parser.add_argument("--week-start", help="Target Monday as YYYY-MM-DD; defaults to current week")
    parser.add_argument("--seed", type=int, help="Deterministic random seed")
    parser.add_argument("--force", action="store_true", help="Regenerate an existing week")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = run_scheduler(
        participants_path=args.participants,
        schedule_path=args.schedule,
        history_path=args.history,
        output_dir=args.output_dir,
        week_start=args.week_start,
        seed=args.seed,
        force=args.force,
    )
    print(
        f"random-coffee status={result.status} week_start={result.week_start} "
        f"pairings={result.pairing_count} events_path={result.events_path or '-'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
