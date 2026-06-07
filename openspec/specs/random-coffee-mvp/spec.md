# random-coffee-mvp Specification

## Purpose

Provide a repository-native MVP for weekly random coffee pairings: YAML input, history-aware pairing, mock Google Calendar invite output, and GitHub Actions automation.

## Requirements

### Requirement: YAML participant registry
The system SHALL load participants from `config/participants.yaml` and include only active participants.

#### Scenario: fifty active participants
- **GIVEN** 50 active participants
- **WHEN** the scheduler runs for a new week
- **THEN** it produces 25 pairings
- **AND** each participant appears exactly once

#### Scenario: duplicate email
- **GIVEN** two active participants with the same email after case/whitespace normalisation
- **WHEN** config is loaded
- **THEN** validation fails

### Requirement: history-aware matching
The system SHALL avoid repeated pairings when a non-repeat pairing is possible.

#### Scenario: previous pairing exists
- **GIVEN** Alice and Bob were paired in history
- **WHEN** alternatives are available
- **THEN** Alice and Bob are not paired again

### Requirement: weekly idempotency
The system SHALL not duplicate invites/history for an already completed week unless `--force` is passed.

#### Scenario: rerun same week
- **GIVEN** `data/history.yaml` already contains the target week
- **WHEN** the scheduler runs without `--force`
- **THEN** it exits with a skipped status
- **AND** does not write additional events

### Requirement: mock calendar event generation
The system SHALL create one mock event per generated pairing.

#### Scenario: pair event
- **GIVEN** a pairing with two participants
- **WHEN** events are created
- **THEN** the event contains exactly those attendees
- **AND** start/end times are 15 minutes apart
- **AND** the description explains participant-led rescheduling

### Requirement: GitHub Actions scheduler
The repository SHALL include a workflow that runs tests, executes the scheduler weekly, and commits generated history/output changes.

#### Scenario: weekly workflow
- **GIVEN** the workflow runs on Monday morning
- **WHEN** tests pass
- **THEN** the scheduler is executed for the current week
- **AND** any changed `data/history.yaml` and `output/mock-calendar-events/*.json` files are committed
